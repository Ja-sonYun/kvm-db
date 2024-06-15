from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from kvm_db.backends.base import DatabaseBackend


class Sqlite(DatabaseBackend):
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def remove(self) -> None:
        if self.db_path is None:
            raise ValueError("Database path must be provided")

        if self.db_path.exists():
            self.db_path.unlink()

    @contextmanager
    def _connect(
        self,
        commit: bool = True,
    ) -> Generator[sqlite3.Connection, None, None]:
        if self.db_path is None:
            raise ValueError("Database path must be provided")

        conn = sqlite3.connect(self.db_path)
        yield conn
        if commit:
            conn.commit()

        conn.close()

    def _create_table(self, name: str, ttl: int | None = None) -> None:
        if ttl is not None:
            raise ValueError("Sqlite does not support TTL")
        with self._connect() as conn:
            conn.cursor().execute(f"CREATE TABLE IF NOT EXISTS {name} " "(key TEXT PRIMARY KEY, value TEXT)")

    def _get_tables(self) -> list[str]:
        with self._connect(commit=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            result = cursor.fetchall()

        return [table[0] for table in result]

    def _insert_datum(
        self,
        table: str,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        if ttl is not None:
            raise ValueError("Sqlite does not support TTL")
        with self._connect() as conn:
            conn.cursor().execute(
                f"REPLACE INTO {table} (key, value) VALUES (?, ?)",
                (key, value),
            )

    def _delete_datum(self, table: str, key: str) -> None:
        with self._connect() as conn:
            conn.cursor().execute(f"DELETE FROM {table} WHERE key = ?", (key,))

    def _get_datum(self, table: str, key: str) -> str | None:
        with self._connect(commit=False) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT value FROM {table} WHERE key = ?", (key,))
            result = cursor.fetchone()

        return result[0] if result else None

    def _get_all_data(self, table: str) -> list[tuple[str, str]]:
        with self._connect(commit=False) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT key, value FROM {table}")
            result = cursor.fetchall()

        return result

    def _update_datum(self, table: str, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.cursor().execute(
                f"UPDATE {table} SET value = ? WHERE key = ?",
                (value, key),
            )
