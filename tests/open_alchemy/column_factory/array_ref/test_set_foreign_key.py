"""Tests for _set_foreign_key."""
# pylint: disable=protected-access

from unittest import mock

import pytest
import sqlalchemy

from open_alchemy import exceptions
from open_alchemy import types
from open_alchemy.column_factory import array_ref


@pytest.mark.column
@pytest.mark.array_ref
def test_set_foreign_key_schemas_missing():
    """
    GIVEN referenced model is not in models and not in schemas
    WHEN _set_foreign_key is called with the referenced model name
    THEN MalformedRelationshipError is raised.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="column_1",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )
    model_schema = {
        "type": "object",
        "x-tablename": "schema",
        "properties": {artifacts.fk_column_name: {"type": "integer"}},
    }

    with pytest.raises(exceptions.MalformedRelationshipError):
        array_ref._set_foreign_key(
            artifacts=artifacts, model_schema=model_schema, schemas={}
        )


@pytest.mark.column
@pytest.mark.array_ref
def test_set_foreign_key_schemas():
    """
    GIVEN referenced model is not in models, model schema, schemas and foreign key
        column
    WHEN _set_foreign_key is called with the model schema, schemas and foreign key
        column
    THEN the foreign key column is added to the referenced model using allOf.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="column_1",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )
    tablename = "schema"
    model_schema = {
        "type": "object",
        "x-tablename": tablename,
        "properties": {artifacts.fk_column_name: {"type": "integer"}},
    }
    schemas = {artifacts.ref_model_name: {"type": "object", "properties": {}}}

    array_ref._set_foreign_key(
        artifacts=artifacts, model_schema=model_schema, schemas=schemas
    )

    assert schemas == {
        artifacts.ref_model_name: {
            "allOf": [
                {"type": "object", "properties": {}},
                {
                    "type": "object",
                    "properties": {
                        f"{tablename}_{artifacts.fk_column_name}": {
                            "type": "integer",
                            "x-foreign-key": f"{tablename}.{artifacts.fk_column_name}",
                            "x-dict-ignore": True,
                        }
                    },
                },
            ]
        }
    }


@pytest.mark.column
@pytest.mark.array_ref
def test_set_foreign_key_models(mocked_facades_models: mock.MagicMock):
    """
    GIVEN mocked models, referenced model is in models, model schema, schemas and
        foreign key column
    WHEN _set_foreign_key is called with the model schema, schemas and foreign key
        column
    THEN the foreign key is added to the model.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="column_1",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )
    tablename = "schema"
    model_schema = {
        "type": "object",
        "x-tablename": tablename,
        "properties": {artifacts.fk_column_name: {"type": "integer"}},
    }
    schemas = {artifacts.ref_model_name: {"type": "object", "properties": {}}}
    mock_ref_model = mock.MagicMock()
    mocked_facades_models.get_model.return_value = mock_ref_model

    array_ref._set_foreign_key(
        artifacts=artifacts, model_schema=model_schema, schemas=schemas
    )

    added_fk_column = getattr(mock_ref_model, f"{tablename}_{artifacts.fk_column_name}")
    assert isinstance(added_fk_column.type, sqlalchemy.Integer)
    foreign_key = list(added_fk_column.foreign_keys)[0]
    assert f"{tablename}.{artifacts.fk_column_name}" in str(foreign_key)
    mocked_facades_models.get_model.assert_called_once_with(
        name=artifacts.ref_model_name
    )
