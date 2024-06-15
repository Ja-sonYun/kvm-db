# kvm-db

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/kvm-db/0.1.5)](https://pypi.org/project/kvm-db/) [![PyPI version](https://badge.fury.io/py/kvm-db.svg)](https://badge.fury.io/py/kvm-db)

kvm-db is a Python library that provides a simple interface for both key-value storage and model-based data management using SQLite.

## Features

- Key-Value Store: Simple API for key-value data operations.
- Model Database: Manage data using Python classes and objects.

### Supported Backends

#### SQLite

```sh
pip install 'kvm-db'
```

```python
from kvm_db import Sqlite

backend = Sqlite("db.sqlite")
```

#### DynamoDB

```sh
pip install 'kvm-db[dynamodb]'
```

```python
from kvm_db import DynamoDB

backend = DynamoDB("table_name")
```

Terrform example for creating a DynamoDB table:

```hcl
module "kv_table" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "4.0.1"

  name     = "example-keyval-table"
  hash_key = "key"

  attributes = [
    {
      name = "key"
      type = "S"
    },
    {
      name = "table"
      type = "S"
    },
  ]

  global_secondary_indexes = [
    {
      name            = "table-index"
      hash_key        = "table"
      projection_type = "ALL"
    }
  ]

  # If you want to enable TTL
  ttl_attribute_name = "ttl"
  ttl_enabled        = true
}

```

You can insert datum with ttl attribute like this:

```python
kv_db.insert_datum(TABLE, KEY, VALUE, ttl=10)  # 10 seconds
```

#### SQLs

TODO

#### JsonDB

TODO

## Installation

Install kvm-db using pip:

```bash
pip install kvm-db
```

## Quick Start

You can retrieve the value using this syntax

```python
db[TABLE_NAME, KEY]
# Or
table_db = db[TABLE_NAME]
table_db[KEY]
```

Below is a quick example to get you started with kvm-db.

### Key-Value Database Example

```python
from kvm_db import KeyValDatabase, Sqlite

# Initialize the database with SQLite
kv_db = KeyValDatabase(Sqlite("kv.db"))

# Create a new table
kv_db.create_table("test_table")

# Adding and accessing data
kv_db["test_table", "key1"] = "value1"
kv_db["test_table"]["key2"] = "value2"

# Retrieve all items in the table
print(kv_db["test_table", :])  # Output: [('key1', 'value1'), ('key2', 'value2')]

# Update and delete data
kv_db["test_table", "key1"] = "updated_value"
del kv_db["test_table", "key1"]

# Check the table after deletion
print(kv_db["test_table", :])  # Output: []
```

### Model(`Pydantic`) Database Example

TODO: Support native Python dataclasses and other data types.

```python
from kvm_db import ModelDatabase, Sqlite, TableModel

class User(TableModel):
    name: str


# Initialize Model Database with SQLite
model_db_backend = Sqlite("model.db")
model_db = ModelDatabase(model_db_backend)

# Register the model
model_db.register(User)

# Create and insert a new user
user1 = User(name="Alice")
model_db.insert(user1)

# Query users
all_users = model_db[User][:]
print(all_users[0].name)  # Output: Alice

# Query user with id
alice_id = user1.id
alice = model_db[User][alice_id]
print(alice.name)  # Output: Alice

# Update user information
alice.name = "Bob"
alice.commit()

# Confirm update
print(model_db[User, :][0].name)  # Output: Bob

# Delete a user
user1.delete()
print(model_db[User, :])  # Output: []
```
