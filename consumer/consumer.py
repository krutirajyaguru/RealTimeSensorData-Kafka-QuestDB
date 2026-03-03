import psycopg
from questdb.ingress import Sender, TimestampNanos
import time
import random
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.errors import NoBrokersAvailable

# Use the service name defined in docker-compose
HOST = 'questdb' 
PG_PORT = 8812
ILP_PORT = 9000
BOOTSTRAP = "broker:29092"
TOPIC='sensor-data-topic'
TABLE='sensor_data'

def wait_for_kafka():
    while True:
        try:
            KafkaConsumer(bootstrap_servers=BOOTSTRAP)
            print("Kafka is ready")
            return
        except NoBrokersAvailable:
            print("Kafka not ready, retrying...")
            time.sleep(5)

# --- 3. Wait for kafka-topic ---
def wait_for_topic():
    while True:
        try:
            admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)
            if TOPIC in admin.list_topics():
                print("Kafka topic is ready")
                return
            print("Waiting for Kafka topic...")
        except Exception:
            pass
        time.sleep(2)

wait_for_kafka()
wait_for_topic()       
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP,
    auto_offset_reset="latest",
    enable_auto_commit=True
)

def run_automation():
    # Wait for QuestDB to be ready
    #time.sleep(5) 
    
    conn_str = f'user=admin password=quest host={HOST} port={PG_PORT} dbname=qdb'
    
    try:
        with psycopg.connect(conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                print("Dropping table if it exists...")
                cur.execute('DROP TABLE IF EXISTS sensor_data;')
                
                print("Creating table...")
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        ts TIMESTAMP,
                        sequence_number LONG,
                        objects STRING,
                        x DOUBLE,
                        y DOUBLE,
                        z DOUBLE
                    ) TIMESTAMP(ts) PARTITION BY DAY WAL;
                ''')
        
        conf = f'http::addr={HOST}:{ILP_PORT};'

        for msg in consumer:
            print(f"Received message: {len(msg.value)} bytes")
            import pyarrow.ipc as ipc
            from io import BytesIO
            import time

            reader = ipc.open_stream(BytesIO(msg.value))
            base_ts = time.time_ns()

            
                
            for batch in reader:
                cols = {f.name: batch.column(i) for i, f in enumerate(batch.schema)}
                sequence_number = cols["sequence_number"].to_numpy(zero_copy_only=False)
                objects = cols["objects"]
                x = cols["x"]
                y = cols["y"]
                z = cols["z"]

                with Sender.from_conf(conf) as sender:
                    print("Ingesting data...")
                    for i in range(batch.num_rows):
                        sender.row(
                            TABLE,
                            #symbols={"objects": objects[i].as_py()},
                            columns={
                                "sequence_number": int(sequence_number[i]),
                                "objects": str(objects[i].as_py()),
                                "x": float(x[i].as_py()),
                                "y": float(y[i].as_py()),
                                "z": float(z[i].as_py())
                            },
                            at=TimestampNanos.now()  # <- this fills ts column
                        )
                    sender.flush()
                    print("Success!")
            # with Sender.from_conf(conf) as sender:
            #     print("Ingesting data...")
            #     for i in range(50):
            #         sender.row(
            #             'sensor_data',
            #             symbols={'sensor_name': 'zone_1'},
            #             columns={'reading': random.uniform(20.0, 30.0)},
            #             at=TimestampNanos.now()
            #         )
            #     sender.flush()
            #     print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_automation()