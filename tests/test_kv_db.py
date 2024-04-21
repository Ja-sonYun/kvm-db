import tempfile
from collections.abc import Generator

import pytest

from kvm_db.backends.sqlite import Sqlite
from kvm_db.kv_db import KeyValDatabase


@pytest.fixture
def sqlite_db() -> Generator[Sqlite, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False).name

        sqlite = Sqlite(db_path)
        sqlite._create_table("test_table")

        yield sqlite


@pytest.fixture
def keyval_db(sqlite_db: Sqlite) -> KeyValDatabase:
    return KeyValDatabase(sqlite_db)


def test_keyval_create_table(keyval_db: KeyValDatabase) -> None:
    # Test creating a table
    keyval_db.create_table("test_table_2")
    assert "test_table_2" in keyval_db._backend._get_tables()


def test_keyval_get_set_item(keyval_db: KeyValDatabase) -> None:
    # Test __setitem__ and __getitem__ for single key-value
    keyval_db["test_table", "key1"] = "value1"
    assert keyval_db["test_table", "key1"] == "value1"


def test_keyval_get_all_data(keyval_db: KeyValDatabase) -> None:
    # Test retrieving all data from a table
    keyval_db["test_table", "key1"] = "value1"
    keyval_db["test_table", "key2"] = "value2"
    assert keyval_db["test_table", :] == [("key1", "value1"), ("key2", "value2")]


def test_keyval_update_data(keyval_db: KeyValDatabase) -> None:
    # Test updating an existing key
    keyval_db["test_table", "key1"] = "value1"
    keyval_db["test_table", "key1"] = "updated_value"
    assert keyval_db["test_table", "key1"] == "updated_value"


def test_keyval_delete_data(keyval_db: KeyValDatabase) -> None:
    # Test __delitem__ for a single key
    keyval_db["test_table", "key1"] = "value1"
    del keyval_db["test_table", "key1"]
    with pytest.raises(KeyError):
        _ = keyval_db["test_table", "key1"]


def test_keyval_delete_all_data(keyval_db: KeyValDatabase) -> None:
    # Test deleting all data from a table
    keyval_db["test_table", "key1"] = "value1"
    keyval_db["test_table", "key2"] = "value2"
    del keyval_db["test_table", :]
    assert keyval_db.get_all_data("test_table") == []


def test_keyval_error_on_nonexistent_key(keyval_db: KeyValDatabase) -> None:
    # Test error handling for non-existent key
    with pytest.raises(KeyError):
        _ = keyval_db["test_table", "nonexistent_key"]


def test_keyval_error_on_invalid_set(keyval_db: KeyValDatabase) -> None:
    # Test error handling for invalid set operation
    with pytest.raises(ValueError):
        keyval_db["test_table"] = "value"


def test_keyval_table_get_set_item(keyval_db: KeyValDatabase) -> None:
    # Testing _KeyValTable functionality
    table = keyval_db["test_table"]
    table["key1"] = "value1"
    assert table["key1"] == "value1"


def test_keyval_table_delete_item(keyval_db: KeyValDatabase) -> None:
    # Testing _KeyValTable delete functionality
    table = keyval_db["test_table"]
    table["key1"] = "value1"
    del table["key1"]
    with pytest.raises(KeyError):
        _ = table["key1"]
