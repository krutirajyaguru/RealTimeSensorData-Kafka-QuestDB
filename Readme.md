# Real-Time Radar Streaming Project – Overview

## Goal

Build a containerized real-time data pipeline that:

1. Produces radar sensor data to Kafka  
2. Consumes Kafka data  
3. Converts **wide format → long format** using PyArrow  
4. Stores transformed data in QuestDB  
5. Runs everything inside Docker  

---

# Data Model

## Input (Wide Format)

Sensor detects up to 16 objects per frame:

    +-----------+-----------+-----------+ ... +------------+
    | Tracker0  | Tracker1  | Tracker2  | ... | Tracker15  |
    +-----------+-----------+-----------+ ... +------------+
    | 0.32      | 0.55      | 0.35      | ... | 0.71       | ---> x_values
    +-----------+-----------+-----------+ ... +------------+
    | 0.16      | 0.57      | 0.33      | ... | 0.47       | ---> y_values
    +-----------+-----------+-----------+ ... +------------+
    | 0.12      | 0.955     | 0.33      | ... | 0.73       | ---> z_values
    +-----------+-----------+-----------+ ... +------------+
Problems:
- Hard to scale
- Schema changes if object limit changes
- Not efficient for analytics

---

## Output (Long Format)


    +-----------+-------+-------+-------+-------------------+------------------------------+
    | objects   |   x   |   y   |   z   | sequence_number   | timestamp                    |
    +-----------+-------+-------+-------+-------------------|------------------------------|
    |     0     | 0.12  | 0.44  | 0.88  |  1                | 2026-03-03T12:32:05.576400Z  |
    |     1     | 0.55  | 0.11  | 0.72  |  1                | 2026-03-03T12:32:05.576400Z  |
    |   ...     |  ...  |  ...  |  ...  |  ...              | 2026-03-03T12:32:05.576400Z  |
    |    15     | 0.77  | 0.61  | 0.09  |  1                | 2026-03-03T12:32:05.576400Z  |
    +--------------------------------------------------------------------------------------+ 

Benefits:
- Scalable
- Query-friendly
- Works better in QuestDB
- Easier for visualization

---


# Why PyArrow?

PyArrow allows:

- Columnar transformation
- Vectorized operations
- Fast reshaping
- Efficient memory handling

Instead of Python loops:

Slow
```
for tracker in trackers:
```

Use Arrow column operations:
- Reshape
- Stack columns
- Explode object index

Much faster for high-frequency data.

---

# Docker Setup Overview

## Services

- kafka 
- questdb
- producer
- consumer

All inside one `docker-compose.yml`.

---

# Project Structure

```
project/
│
├── docker-compose.yml
│
├── README.md
│
├── producer/
│   ├── Dockerfile
│   └── producer.py
│
├── consumer/
    ├── Dockerfile
    └── consumer.py
    └── README.md

```

---
