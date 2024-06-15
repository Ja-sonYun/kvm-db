from __future__ import annotations

import uuid
from typing import Generic, Optional, TypeVar, Union, cast, overload

from pydantic import BaseModel, Field, PrivateAttr

from kvm_db.backends.base import DatabaseBackend


class TableModel(BaseModel):
    _database: Optional["ModelDatabase"] = PrivateAttr(default=None)

    id: str = Field(frozen=True, default_factory=lambda: str(uuid.uuid4()))

    def commit(self) -> None:
        if self._database is None:
            raise ValueError("Database not set")
        self._database.update(self)

    def delete(self) -> None:
        if self._database is None:
            raise ValueError("Database not set")
        self._database.delete(self)


_gDatum = TypeVar("_gDatum", bound=TableModel)


class ModelDatabase:
    def __init__(self, backend: DatabaseBackend) -> None:
        self._backend = backend

    def register(self, model: type[TableModel], *, ttl: int | None = None) -> None:
        self._backend._create_table(model.__name__, ttl=ttl)

    def insert(self, model: TableModel, *, ttl: int | None = None) -> None:
        serialzied = model.model_dump_json(exclude={"_databse"})
        self._backend._insert_datum(model.__class__.__name__, model.id, serialzied, ttl)
        model._database = self

    def delete(
        self,
        model: TableModel | type[TableModel],
        id: str | None = None,
    ) -> None:
        if isinstance(model, type):
            if id is None:
                raise ValueError("id must be provided to delete table")
            self._backend._delete_datum(model.__name__, id)
        else:
            self._backend._delete_datum(model.__class__.__name__, model.id)
            model._database = None

    def get_datum(
        self,
        model_type: type[_gDatum],
        id: str,
    ) -> _gDatum:
        model_data = self._backend._get_datum(model_type.__name__, id)
        if model_data is None:
            raise KeyError(f"Model {model_type.__name__} with id {id} not found")
        datum = model_type.model_validate_json(model_data)
        datum._database = self
        return datum

    def get_all_data(self, model_type: type[_gDatum]) -> list[_gDatum]:
        all_data = self._backend._get_all_data(model_type.__name__)
        data = [model_type.model_validate_json(data[1]) for data in all_data]
        for datum in data:
            datum._database = self
        return data

    def update(self, model: TableModel) -> None:
        if model._database is None:
            raise ValueError("Disconnect model from database")
        self._backend._update_datum(
            model.__class__.__name__,
            model.id,
            model.model_dump_json(),
        )

    @overload
    def __getitem__(self, query: tuple[type[_gDatum], slice]) -> list[_gDatum]: ...

    @overload
    def __getitem__(self, query: tuple[type[_gDatum], str]) -> _gDatum: ...

    @overload
    def __getitem__(self, query: tuple[type[_gDatum], str | slice]) -> _gDatum | list[_gDatum]: ...

    @overload
    def __getitem__(self, query: slice) -> TableModel: ...

    @overload
    def __getitem__(self, query: type[_gDatum]) -> "ModelTable[_gDatum]": ...

    def __getitem__(
        self,
        query: type[_gDatum] | tuple[type[_gDatum], str | slice] | slice,
    ) -> Union[_gDatum, "ModelTable[_gDatum]", list[_gDatum]]:
        if isinstance(query, type):
            return ModelTable(self, query)
        elif isinstance(query, slice):
            table = cast(type[_gDatum], query.start)
            key = cast(str, query.stop)
        else:
            table, key_or_range = query
            if isinstance(key_or_range, slice):
                if any([key_or_range.start, key_or_range.stop]):
                    raise ValueError("You can only use `:` to retrieve all data.")

                return self.get_all_data(table)
            key = key_or_range

        datum = self.get_datum(table, key)
        if datum is None:
            raise KeyError(f"Key {key} not found in table {table}")

        return datum


class ModelTable(Generic[_gDatum]):
    def __init__(self, kv_db: ModelDatabase, model: type[_gDatum]) -> None:
        self.kv_db = kv_db
        self.model = model

    @overload
    def __getitem__(self, key: str) -> _gDatum: ...

    @overload
    def __getitem__(self, key: slice) -> list[_gDatum]: ...

    def __getitem__(self, key: str | slice) -> _gDatum | list[_gDatum]:
        return self.kv_db[self.model, key]

    def update(self, value: _gDatum) -> None:
        self.kv_db.update(value)

    def delete(self, key: str | _gDatum) -> None:
        obj_id = key.id if isinstance(key, TableModel) else key
        self.kv_db.delete(self.model, obj_id)
