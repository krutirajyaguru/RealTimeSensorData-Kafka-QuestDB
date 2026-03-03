# QuestDB Docker 

## Important

QuestDB does **NOT** auto-execute `init.sql` files like Postgres or MySQL.

Mounting `init.sql` into the container does nothing.

There is **no supported "run SQL on startup" mechanism**.

Filesystem warnings such as:

- `Unsupported file system`
- `vm.max_map_count`

are **NOT related to table creation**.

---

## Correct Way to Create Tables Automatically

Always create tables programmatically via the HTTP `/exec` endpoint **before ingestion starts**.

### Correct Order

1. Wait for QuestDB HTTP to be ready  
2. Run:

```
CREATE TABLE IF NOT EXISTS ...
```

3. Only then start ILP / ingestion

---

## 🔧 Example

```
GET http://questdb:9000/exec?query=CREATE TABLE IF NOT EXISTS my_table (...)
```

---

## Why This Works

- Officially supported by QuestDB
- Works in Docker
- Works in CI pipelines
- Works in Kubernetes
- Prevents `table does not exist`
- Prevents ILP `Sender is closed` errors

---

## What To Avoid

- `init.sql` volume mounts
- Assuming QuestDB behaves like Postgres
- Starting ILP before the table exists

---

## Rule of Thumb

> In QuestDB, tables are created via SQL API or ingestion —  
> never via `init.sql` files.

---

## Web Console

To check tables, queries, and data:

```
http://127.0.0.1:9000
```

Open this in your browser to access the QuestDB UI.