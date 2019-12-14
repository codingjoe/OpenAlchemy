"""Tests for calculating the foreign key artifacts."""
# pylint: disable=protected-access

import pytest

from open_alchemy import exceptions
from open_alchemy.column_factory import object_ref


@pytest.mark.parametrize(
    "schema, schemas, fk_column",
    [
        ({"properties": {"id": {}}}, {}, "id"),
        ({"x-tablename": "table 1"}, {}, "id"),
        ({"x-tablename": "table 1", "properties": {}}, {}, "id"),
        (
            {"x-tablename": "table 1", "properties": {"id": {"type": "integer"}}},
            {},
            "column_1",
        ),
        ({"x-tablename": "table 1", "properties": {"id": {}}}, {}, "id"),
    ],
    ids=[
        "no tablename",
        "no properties",
        "no id property",
        "custom foreign key property missing",
        "id property no type",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_malformed_schema(schema, schemas, fk_column):
    """
    GIVEN schema, schemas and foreign key column
    WHEN _calc_fk_artifacts is called with the schema, schemas and foreign key
        column
    THEN a MalformedSchemaError is raised.
    """
    with pytest.raises(exceptions.MalformedSchemaError):
        object_ref._calc_fk_artifacts(
            model_schema=schema, schemas=schemas, fk_column_name=fk_column
        )


@pytest.mark.column
@pytest.mark.object_ref
def test_fk_return():
    """
    GIVEN foreign key column and object schema with x-tablename and id and foreign key
        property with a type
    WHEN _calc_fk_artifacts is called with the schema
    THEN a schema with the type of the foreign key property and x-foreign-key property.
    """
    model_schema = {
        "x-tablename": "table 1",
        "properties": {"id": {"type": "idType"}, "fk": {"type": "fkType"}},
    }
    schemas = {}

    return_value = object_ref._calc_fk_artifacts(
        model_schema=model_schema, schemas=schemas, fk_column_name="fk"
    )

    assert return_value.type == "fkType"
    assert return_value.foreign_key == "table 1.fk"
