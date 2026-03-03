# FROM python:3.11-slim

# WORKDIR /app

# RUN pip install --no-cache-dir \
#     numpy \
#     pyarrow \
#     kafka-python  

# COPY producer.py .
# COPY data/sensor_data.csv /data/sensor_data.csv   

# CMD ["python", "producer.py"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir numpy pyarrow kafka-python

# Copy producer code AND CSV
COPY producer.py .
COPY data/sensor_data.csv /data/sensor_data.csv   

CMD ["python", "producer.py"]
