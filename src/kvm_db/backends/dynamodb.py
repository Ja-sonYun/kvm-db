from __future__ import annotations

import json
from time import time
from typing import TYPE_CHECKING

import boto3

from kvm_db.backends.base import DatabaseBackend

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.client import DynamoDBClient


class DynamoDB(DatabaseBackend):
    """
    DynamoDB backend for the DatabaseBackend.

    Table and key fields needs to be hashable.
    """

    __meta_table_name__ = "__kvm_db_meta__"
    __table_key__ = "__registered_tables__"

    def __init__(
        self,
        table_name: str,
        args: dict[str, str] | None = None,
    ) -> None:
        self.table_name = table_name
        self.client_args = args or {}

        self._registered_tables = set[tuple[str, int | None]]()
        self._create_table(self.__meta_table_name__)

    def _get_client(self) -> "DynamoDBClient":
        return boto3.client(
            "dynamodb",
            **self.client_args,  # type: ignore
        )

    def _create_table(self, name: str, ttl: int | None = None) -> None:
        """
        Note that this method does not actually create a table in DynamoDB.
        """
        if name in self._get_tables(remote=False):
            raise ValueError(f"Table {name} already exists")

        self._registered_tables.add((name, ttl))
        tables = self._get_tables(remote=False)
        value = json.dumps(tables)
        self._insert_datum(self.__meta_table_name__, self.__table_key__, value)

    def _ensure_table_registered(self, table: str) -> None:
        if table not in self._get_tables(remote=False):
            raise ValueError(f"Table {table} is not registered")

    def _get_tables(self, *, remote: bool = False) -> list[str]:
        if remote:
            raw_tables = self._get_datum(self.__meta_table_name__, self.__table_key__)
            tables: list[str] = json.loads(raw_tables) if raw_tables is not None else []
            return tables
        return [item[0] for item in self._registered_tables]

    def _insert_datum(
        self,
        table: str,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        self._ensure_table_registered(table)

        item: dict[str, dict[str, str | int]] = {
            "table": {"S": table},
            "key": {"S": key},
            "value": {"S": value},
        }
        table_ttl = next((item[1] for item in self._registered_tables if item[0] == table), None)
        if ttl is not None or table_ttl is not None:
            item_ttl: int
            # Prefer the ttl argument over the table ttl
            if ttl is not None:
                item_ttl = ttl
            elif table_ttl is not None:
                item_ttl = table_ttl
            else:
                raise ValueError("We should never reach this point.")
            item["ttl"] = {"N": str(int(time() + item_ttl))}

        client = self._get_client()
        client.put_item(TableName=self.table_name, Item=item)

    def _delete_datum(self, table: str, key: str) -> None:
        self._ensure_table_registered(table)

        client = self._get_client()
        client.delete_item(
            TableName=self.table_name,
            Key={"table": {"S": table}, "key": {"S": key}},
        )

    def _get_datum(self, table: str, key: str) -> str | None:
        self._ensure_table_registered(table)

        client = self._get_client()
        response = client.get_item(
            TableName=self.table_name,
            Key={"table": {"S": table}, "key": {"S": key}},
        )
        return response.get("Item", {}).get("value", {}).get("S")

    def _get_all_data(self, table: str) -> list[tuple[str, str]]:
        self._ensure_table_registered(table)

        client = self._get_client()
        response = client.scan(TableName=self.table_name)
        items = response.get("Items", [])
        current_timestamp = int(time())
        kv_pairs: list[tuple[str, str]] = []
        for item in items:
            item_table = item["table"].get("S")
            if item_table != table:
                continue
            ttl = item.get("ttl", {}).get("N")
            if ttl is not None and int(ttl) < current_timestamp:
                continue
            key = item["key"].get("S")
            value = item["value"].get("S")
            if key is not None and value is not None:
                kv_pairs.append((key, value))

        return kv_pairs

    def _update_datum(self, table: str, key: str, value: str) -> None:
        self._ensure_table_registered(table)

        client = self._get_client()
        client.update_item(
            TableName=self.table_name,
            Key={"table": {"S": table}, "key": {"S": key}},
            UpdateExpression="SET value = :val",
            ExpressionAttributeValues={":val": {"S": value}},
        )
