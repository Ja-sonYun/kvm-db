import tempfile
from collections.abc import Generator

import pytest

from kvm_db.backends.sqlite import Sqlite


@pytest.fixture
def sqlite_db() -> Generator[Sqlite, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False).name

        yield Sqlite(db_path)


def test_db_connection_context(sqlite_db: Sqlite) -> None:
    with sqlite_db._connect() as conn:
        assert conn is not None
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test (id) VALUES (1)")
        conn.commit()

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM test")
        result = cursor.fetchone()
        assert result[0] == 1


def test_create_table(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    with sqlite_db._connect(commit=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
        assert cursor.fetchone()


def test_get_tables(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    tables = sqlite_db._get_tables()
    assert "test_table" in tables


def test_insert_data(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    sqlite_db._insert_datum("test_table", "key1", "value1")
    with sqlite_db._connect(commit=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM test_table WHERE key = ?", ("key1",))
        assert cursor.fetchone()[0] == "value1"


def test_delete_data(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    sqlite_db._insert_datum("test_table", "key1", "value1")
    sqlite_db._delete_datum("test_table", "key1")
    with sqlite_db._connect(commit=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM test_table WHERE key = ?", ("key1",))
        assert cursor.fetchone() is None


def test_get_datum(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    sqlite_db._insert_datum("test_table", "key1", "value1")
    result = sqlite_db._get_datum("test_table", "key1")
    assert result == "value1"


def test_get_all_data(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    sqlite_db._insert_datum("test_table", "key1", "value1")
    sqlite_db._insert_datum("test_table", "key2", "value2")
    result = sqlite_db._get_all_data("test_table")
    assert result == [("key1", "value1"), ("key2", "value2")]


def test_update_data(sqlite_db: Sqlite) -> None:
    sqlite_db._create_table("test_table")
    sqlite_db._insert_datum("test_table", "key1", "value1")
    sqlite_db._update_datum("test_table", "key1", "updated_value")
    result = sqlite_db._get_datum("test_table", "key1")
    assert result == "updated_value"
