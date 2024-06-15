from __future__ import annotations

from abc import ABC, abstractmethod


class DatabaseBackend(ABC):
    @abstractmethod
    def _create_table(self, name: str, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    def _get_tables(self) -> list[str]:
        pass

    @abstractmethod
    def _insert_datum(
        self,
        table: str,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        pass

    @abstractmethod
    def _delete_datum(self, table: str, key: str) -> None:
        pass

    @abstractmethod
    def _get_datum(self, table: str, key: str) -> str | None:
        pass

    @abstractmethod
    def _get_all_data(self, table: str) -> list[tuple[str, str]]:
        pass

    @abstractmethod
    def _update_datum(self, table: str, key: str, value: str) -> None:
        pass
