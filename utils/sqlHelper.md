## Examples of ConnDatabase Methods Usage

### Database Connection Establish.

```python
from sqlHelper import ConnDatabase

try:
    db = ConnDatabase("my_database")
    result = db.fetchone("SELECT 1 FROM `users`")
    print(result)
except EnvironmentError as e:
    print(f"Configuration error: {e}")
except MySQLdb.Error as e:
    print(f"Database error: {e}")
finally:
    db.close()  # Explicit cleanup (or use 'with')
```

### Table Metadata

```python
db = ConnDatabase("my_database")

# Safe table creation
db.create_if_not_exists("users", "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100)")

# Force recreate table
db.create_new_table("temp_data", "value FLOAT, timestamp DATETIME")

# Get row count
count = db.entry_count("users")
print(f"Total users: {count}")

# Get all tables
tables = db.show_tables()
print("Tables:", tables)

# Get columns for a table
columns = db.show_columns("users")
print("Columns:", columns)
```

### Read

Basic select.
```python
# Get single record as dictionary
user = db.select_one(
    table_name="users",
    fields=["id", "name", "email"],
    condition="id = %s",
    condition_values=(123,)
)

# Get multiple records with pagination
active_users = db.select_all(
    table_name="users",
    fields="*",  # Get all fields
    condition="is_active = %s",
    condition_values=(True,),
    limit=10,
    offset=20,
    order_by="created_at",
    descending=True,
    return_as="dict"
)

# Simple query with just table name
all_users = db.select_all(table_name="users")
```

Special select.
```python
# Simple JOIN
orders_with_customers = db.select_with_join(
    table_name="orders",
    joins=[{
        'table': "customers",
        'on': "orders.customer_id = customers.id"
    }],
    fields=["orders.id", "customers.name", "orders.amount"],
    condition="orders.status = %s",
    condition_values=('completed',)
)

# GROUP BY with aggregates
sales_report = db.select_with_group(
    table_name="orders",
    group_fields=["YEAR(order_date)", "MONTH(order_date)"],
    aggregate_fields=[
        {'field': "id", 'func': "COUNT", 'alias': "order_count"},
        {'field': "amount", 'func': "SUM", 'alias': "total_revenue"}
    ],
    having="total_revenue > %s",
    having_values=(10000,)
)
```

### Insert

```python
row_id = db.insert(
    table_name="users",
    data={
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "is_active": True
    }
)
print(f"Inserted record with ID: {row_id}")
```

### Update

```python
db.update(
    table_name="users",
    data={"name": "Alice", "email": "new@example.com"},
    condition="`id`=%s",
    condition_values=(123,)
) # Update when id equals "123"

db.upsert(
    table_name="users",
    data={"id": 123, "name": "Alice", "email": "new@example.com"},
    condition_field="id"
) # Update when there is already an entry with id "123"; otherwise insert.
```


### Delete

```python
# Delete single record
deleted = db.delete_one(
    "users",
    "id = %s AND status = %s",
    (123, "banned")
)
print(f"Deleted {deleted} record")

# Conditional mass delete
count = db.delete_all(
    "temp_data",
    "created_at < %s",
    ("2022-01-01",)
)
print(f"Deleted {count} old records")

# Batched delete (safe for large tables)
while True:
    deleted = db.delete_all("logs", batch_size=1000)
    print(f"Deleted {deleted} records in this batch")
    if deleted < 1000:
        break

# Full table clearance (explicitly requested)
count = db.delete_all("cache", batch_size=None)  # Safety override
print(f"Cleared entire table ({count} records)")

# Delete the table
db.drop("temp_data")
```

### Primary Key

```python
# Set simple primary key
db.set_primary_key("users", "user_id")

# Set composite primary key
db.set_primary_key("order_items", ["order_id", "product_id"])

# Replace existing primary key
db.set_primary_key("products", "sku", drop_existing=True)

# Remove primary key
db.remove_primary_key("temporary_data")

# Using named constraint
db.set_primary_key(
    "events", 
    "event_id", 
    constraint_name="pk_events",
    drop_existing=True
)
```

### Table combine

```python
# Basic combination
row_count = db.combine_tables(
    "all_products",
    ["products_2022", "products_2023"]
)
print(f"Combined {row_count} rows")

# With filtering
row_count = db.combine_tables(
    "active_users",
    ["users_us", "users_eu"],
    where_clause="status = %s AND last_login > %s",
    where_values=("active", "2023-01-01")
)

# Large table processing
row_count = db.combine_tables(
    "historical_data",
    ["data_q1", "data_q2", "data_q3", "data_q4"],
    chunk_size=50000
)
```