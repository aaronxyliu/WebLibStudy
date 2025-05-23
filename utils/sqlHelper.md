## Examples of ConnDatabase Methods Usage

### Requirement

1. Install the following Python libraries:
    - mysqlclient
    - python-dotenv

2. Create a `.env` file under the root folder to contain all the connection information of the database like the following:
```
DB_HOST=127.0.0.1
DB_USERNAME=root
DB_PASSWORD=12345678
```

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

Special select. (Don't suggest to use since complexity. Put examples here only for dispaly.)
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
    condition_fields="id"
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

### Table Manipulate

Combination.

```python
# Basic combination
row_count = db.combine_tables(
    "all_products", # new table
    ["products_2022", "products_2023"]  # old tables
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

Duplication.
```python
# Full table copy (structure + data + indexes)
row_count = db.duplicate_table("customers", "customers_backup")
print(f"Copied {row_count} rows")

# Create empty template
db.duplicate_table("products", "products_template", copy_data=False)

# Partial copy with filtering
row_count = db.duplicate_table(
    "orders",
    "recent_orders",
    where_clause="order_date > %s",
    where_values=("2023-01-01",)
)

# Large table with chunking
row_count = db.duplicate_table(
    "historical_data",
    "historical_data_copy",
    chunk_size=100000
)
```

Rename.
```python
# Basic rename
if not db.rename_table("old_data", "new_data"):
    print("Target table already exists")

# Forceful rename
db.rename_table("temp_results", "final_results", overwrite=True)
```

Add a column.
```python
# Add simple nullable column
db.add_column("employees", "middle_name", "VARCHAR(100)")

# Drop a column
db.drop_column("employees", "middle_name")

# Add NOT NULL column with default
db.add_column(
    "products",
    "discontinued",
    "BOOLEAN",
    default=False,
    not_null=True
)

# Add positioned column
db.add_column(
    "orders",
    "processing_time",
    "INT",
    after_column="order_date"
)

# Force add even if exists
db.add_column(
    "customers",
    "loyalty_points",
    "INT",
    check_exists=False
)
```