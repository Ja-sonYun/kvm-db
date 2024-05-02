import tempfile
from collections.abc import Generator

import pytest

from kvm_db.backends.sqlite import Sqlite
from kvm_db.model_db import ModelDatabase, ModelTable, TableModel


class ExampleModel(TableModel):
    value: str


@pytest.fixture
def sqlite_db() -> Generator[Sqlite, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False).name

        sqlite = Sqlite(db_path)
        sqlite._create_table("test_table")

        yield sqlite


@pytest.fixture
def model_db(sqlite_db: Sqlite) -> ModelDatabase:
    model = ModelDatabase(sqlite_db)
    model.register(ExampleModel)
    return model


def test_model_insertion_and_retrieval(model_db: ModelDatabase) -> None:
    model_instance = ExampleModel(value="Hello World")
    model_db.insert(model_instance)
    retrieved_model = model_db.get_datum(ExampleModel, model_instance.id)
    assert retrieved_model.value == "Hello World", "Retrieved model should have the correct value."


def test_model_update(model_db: ModelDatabase) -> None:
    model_instance = ExampleModel(value="Initial Value")
    model_db.insert(model_instance)
    model_instance.value = "Updated Value"
    model_instance.commit()
    retrieved_model = model_db.get_datum(ExampleModel, model_instance.id)
    assert retrieved_model.value == "Updated Value", "The model should be updated correctly."


def test_model_deletion(model_db: ModelDatabase) -> None:
    model_instance = ExampleModel(value="To be deleted")
    model_db.insert(model_instance)
    model_db.delete(model_instance)
    with pytest.raises(KeyError):
        model_db.get_datum(ExampleModel, model_instance.id)


def test_model_all_data_retrieval(model_db: ModelDatabase) -> None:
    model1 = ExampleModel(value="First Model")
    model2 = ExampleModel(value="Second Model")
    model_db.insert(model1)
    model_db.insert(model2)
    all_models = model_db.get_all_data(ExampleModel)
    assert len(all_models) == 2, "Should retrieve all models inserted."


def test_error_on_nonexistent_model(model_db: ModelDatabase) -> None:
    with pytest.raises(KeyError):
        model_db.get_datum(ExampleModel, "nonexistent_id")


def test_model_table_access(model_db: ModelDatabase) -> None:
    model_instance = ExampleModel(value="For table access")
    model_db.insert(model_instance)
    model_table = model_db[ExampleModel]
    assert isinstance(model_table, ModelTable), "Should return an instance of _ModelTable."
    retrieved_model = model_table[model_instance.id]
    assert retrieved_model.value == model_instance.value, "Should access and retrieve the correct model."
