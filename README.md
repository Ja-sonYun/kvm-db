# kvm-db

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/kvm-db/0.1.1)](https://pypi.org/project/kvm-db/) [![PyPI version](https://badge.fury.io/py/kvm-db.svg)](https://badge.fury.io/py/kvm-db)

kvm-db is a Python library that provides a simple yet powerful interface for both key-value storage and model-based data management using SQLite. Designed for ease of use, it allows developers to quickly implement robust data storage solutions.

## Features

- Key-Value Store: Simple API for key-value data operations.
- Model Database: Manage data using Python classes and objects.
- Support Type Hinting

#### Supported Backends

- SQLite
TODO: Support for other backends like MySQL, jsondb, etc.

## Installation

Install kvm-db using pip:

```bash
pip install kvm-db
```

## Quick Start

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

### Model Database Example

The Model Database in kvm-db provides an ORM-like interface designed specifically for Pydantic models, facilitating easy data management through object-oriented programming principles.

#### Features

- Pydantic Model Support: Integrates seamlessly with Pydantic to ensure efficient data validation and serialization.
- Serialization and Deserialization: Automatically serializes models to JSON for storage and deserializes JSON back into model instances upon retrieval, simplifying complex data type management.
- Key-Value Underpinnings: The model database fundamentally uses a key-value store approach, enhancing simplicity and scalability.

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
