FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pyarrow \
    requests \
    kafka-python \
    questdb \
    psycopg[binary]

COPY consumer.py .

CMD ["python", "consumer.py"]
