from __future__ import annotations

from typing import Union, overload

from kvm_db.backends.base import FastDatabaseBackend


class KeyValDatabase:
    def __init__(self, backend: FastDatabaseBackend) -> None:
        self._backend = backend

    def create_table(self, name: str) -> None:
        self._backend._create_table(name)

    def insert_datum(self, table: str, key: str, value: str) -> None:
        self._backend._insert_datum(table, key, value)

    def delete_datum(self, table: str, key: str) -> None:
        self._backend._delete_datum(table, key)

    def get_datum(self, table: str, key: str) -> str | None:
        return self._backend._get_datum(table, key)

    def get_all_data(self, table: str) -> list[tuple[str, str]]:
        return self._backend._get_all_data(table)

    def update_datum(self, table: str, key: str, value: str) -> None:
        self._backend._update_datum(table, key, value)

    def tables(self) -> list[str]:
        return self._backend._get_tables()

    @overload
    def __getitem__(self, query: tuple[str, slice]) -> list[tuple[str, str]]: ...

    @overload
    def __getitem__(self, query: tuple[str, str]) -> str: ...

    @overload
    def __getitem__(self, query: tuple[str, str | slice]) -> str | list[tuple[str, str]]: ...

    @overload
    def __getitem__(self, query: slice) -> str: ...

    @overload
    def __getitem__(self, query: str) -> "_KeyValTable": ...

    def __getitem__(
        self,
        query: str | tuple[str, str | slice] | slice,
    ) -> Union[str, "_KeyValTable", list[tuple[str, str]]]:
        if isinstance(query, str):
            return _KeyValTable(self, query)
        elif isinstance(query, slice):
            table = query.start
            key = query.stop
        else:
            table, key = query
            if isinstance(key, slice):
                if any([key.start, key.stop]):
                    raise ValueError("You can only use `:` to retrieve all data.")

                return self.get_all_data(table)

        datum = self.get_datum(table, key)
        if datum is None:
            raise KeyError(f"Key {key} not found in table {table}")

        return datum

    @overload
    def __setitem__(self, query: tuple[str, str], value: str) -> None: ...

    @overload
    def __setitem__(self, query: slice, value: str) -> None: ...

    @overload
    def __setitem__(self, query: str, value: str) -> None: ...

    def __setitem__(
        self,
        query: str | tuple[str, str] | slice,
        value: str,
    ) -> None:
        if isinstance(query, str):
            raise ValueError("Cannot set value for entire table")
        elif isinstance(query, slice):
            table = query.start
            key = query.stop
        else:
            table, key = query

        self.insert_datum(table, key, value)

    @overload
    def __delitem__(self, query: tuple[str, slice]) -> None: ...

    @overload
    def __delitem__(self, query: tuple[str, str]) -> None: ...

    @overload
    def __delitem__(self, query: tuple[str, str | slice]) -> None: ...

    @overload
    def __delitem__(self, query: slice) -> None: ...

    @overload
    def __delitem__(self, query: str) -> None: ...

    def __delitem__(self, query: str | tuple[str, str | slice] | slice) -> None:
        if isinstance(query, str):
            raise ValueError("Cannot delete entire table")
        elif isinstance(query, slice):
            table = query.start
            key = query.stop
        else:
            table, key = query
            if isinstance(key, slice):
                if any([key.start, key.stop]):
                    raise ValueError("You can only use `:` to delete all data.")

                all_keys = self.get_all_data(table)
                for key, _ in all_keys:
                    self.delete_datum(table, key)
                return

        self.delete_datum(table, key)


class _KeyValTable:
    def __init__(self, kv_db: KeyValDatabase, table: str) -> None:
        self.kv_db = kv_db
        self.table = table

    @overload
    def __getitem__(self, key: str) -> str: ...

    @overload
    def __getitem__(self, key: slice) -> list[tuple[str, str]]: ...

    def __getitem__(self, key: str | slice) -> str | list[tuple[str, str]]:
        a = self.kv_db[self.table, key]
        return a

    def __setitem__(self, key: str, value: str) -> None:
        self.kv_db[self.table, key] = value

    @overload
    def __delitem__(self, key: str) -> None: ...

    @overload
    def __delitem__(self, key: slice) -> None: ...

    def __delitem__(self, key: str | slice) -> None:
        del self.kv_db[self.table, key]
