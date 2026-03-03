import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
from kafka import KafkaProducer
import time

# =========================
# CONFIGURATION
# =========================

CSV_PATH = "/data/sensor_data.csv"
KAFKA_TOPIC = "sensor-data-topic"
KAFKA_BROKER = "broker:29092"

LABELS = ('x', 'y', 'z')
GROUP_SIZE = len(LABELS)
SLEEP_SEC = 0.001  # throttle for realism

# =========================
# LOAD CSV ONCE (FINITE SOURCE → UNBOUNDED REPLAY)
# =========================

csv_data = np.genfromtxt(
    CSV_PATH,
    delimiter=",",
    skip_header=1,
    dtype=np.float64,
    filling_values=0.0
)

num_cols = csv_data.shape[1]
col_names = [f"Tracker_{i}" for i in range(num_cols)]

# =========================
# KAFKA PRODUCER
# =========================

# producer = KafkaProducer(
#     bootstrap_servers=KAFKA_BROKER,
#     value_serializer=lambda v: v
# )

MAX_RETRIES = 5

for i in range(MAX_RETRIES):
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: v
        )
        print("Kafka producer connected")
        break
    except Exception:
        print(f"Kafka not ready, retrying {i+1}/{MAX_RETRIES} ...")
        time.sleep(2)
else:
    raise RuntimeError("Cannot connect to Kafka broker")


# =========================
# STREAMING STATE (CRITICAL)
# =========================

sequence_number = 1
row_index = 0

# buffer holds exactly one logical group (x,y,z)
group_buffer = np.zeros((GROUP_SIZE, num_cols), dtype=np.float64)

# =========================
# STREAMING LOOP (UNBOUNDED)
# =========================

while True:
    for row in csv_data:  # replay CSV endlessly
        group_buffer[row_index] = row
        row_index += 1

        # when x,y,z collected → emit
        if row_index == GROUP_SIZE:
            seq_col = np.full(num_cols, sequence_number, dtype=np.int64)
            obj_col = np.asarray(col_names)

            x_vals = group_buffer[0]
            y_vals = group_buffer[1]
            z_vals = group_buffer[2]

            table = pa.Table.from_arrays(
                [
                    pa.array(seq_col),
                    pa.array(obj_col),
                    pa.array(x_vals),
                    pa.array(y_vals),
                    pa.array(z_vals),
                ],
                names=["sequence_number", "objects", "x", "y", "z"]
            )

            # Arrow IPC serialization (zero-copy, fast)‚
            sink = pa.BufferOutputStream()
            with ipc.new_stream(sink, table.schema) as writer:
                writer.write_table(table)

            #print(table)

            producer.send(KAFKA_TOPIC, value=sink.getvalue().to_pybytes())
            producer.flush()
            # advance streaming state
            sequence_number += 1
            row_index = 0
