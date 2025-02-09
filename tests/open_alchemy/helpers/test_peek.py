"""Tests for peek helpers."""

import pytest

from open_alchemy import exceptions
from open_alchemy import helpers


@pytest.mark.parametrize(
    "schema, schemas",
    [({}, {}), ({"type": True}, {})],
    ids=["plain", "not string value"],
)
@pytest.mark.helper
def test_type_no_type(schema, schemas):
    """
    GIVEN schema without a type
    WHEN type_ is called with the schema
    THEN TypeMissingError is raised.
    """
    with pytest.raises(exceptions.TypeMissingError):
        helpers.peek.type_(schema=schema, schemas=schemas)


@pytest.mark.helper
def test_type():
    """
    GIVEN schema with type
    WHEN type_ is called with the schema
    THEN the type of the schema is returned.
    """
    type_ = "type 1"
    schema = {"type": type_}

    returned_type = helpers.peek.type_(schema=schema, schemas={})

    assert returned_type == type_


@pytest.mark.helper
def test_nullable_wrong_type():
    """
    GIVEN schema with nullable defined as a string
    WHEN nullable is called with the schema
    THEN MalformedSchemaError is raised.
    """
    schema = {"nullable": "True"}

    with pytest.raises(exceptions.MalformedSchemaError):
        helpers.peek.nullable(schema=schema, schemas={})


@pytest.mark.parametrize(
    "schema, expected_nullable",
    [({}, None), ({"nullable": True}, True), ({"nullable": False}, False)],
    ids=["missing", "true", "false"],
)
@pytest.mark.helper
def test_nullable(schema, expected_nullable):
    """
    GIVEN schema and expected nullable
    WHEN nullable is called with the schema
    THEN the expected nullable is returned.
    """
    returned_nullable = helpers.peek.nullable(schema=schema, schemas={})

    assert returned_nullable == expected_nullable


@pytest.mark.helper
def test_format_wrong_type():
    """
    GIVEN schema with format defined as a boolean
    WHEN format_ is called with the schema
    THEN MalformedSchemaError is raised.
    """
    schema = {"format": True}

    with pytest.raises(exceptions.MalformedSchemaError):
        helpers.peek.format_(schema=schema, schemas={})


@pytest.mark.parametrize(
    "schema, expected_format",
    [({}, None), ({"format": "format 1"}, "format 1")],
    ids=["missing", "present"],
)
@pytest.mark.helper
def test_format(schema, expected_format):
    """
    GIVEN schema and expected format
    WHEN format_ is called with the schema
    THEN the expected format is returned.
    """
    returned_format = helpers.peek.format_(schema=schema, schemas={})

    assert returned_format == expected_format


@pytest.mark.helper
def test_max_length_wrong_type():
    """
    GIVEN schema with max_length defined as a boolean
    WHEN max_length is called with the schema
    THEN MalformedSchemaError is raised.
    """
    schema = {"maxLength": "1"}

    with pytest.raises(exceptions.MalformedSchemaError):
        helpers.peek.max_length(schema=schema, schemas={})


@pytest.mark.parametrize(
    "schema, expected_max_length",
    [({}, None), ({"maxLength": 1}, 1)],
    ids=["missing", "present"],
)
@pytest.mark.helper
def test_max_length(schema, expected_max_length):
    """
    GIVEN schema and expected max_length
    WHEN max_length is called with the schema
    THEN the expected max_length is returned.
    """
    returned_max_length = helpers.peek.max_length(schema=schema, schemas={})

    assert returned_max_length == expected_max_length


@pytest.mark.helper
def test_read_only_wrong_type():
    """
    GIVEN schema with readOnly defined as a string
    WHEN read_only is called with the schema
    THEN MalformedSchemaError is raised.
    """
    schema = {"readOnly": "true"}

    with pytest.raises(exceptions.MalformedSchemaError):
        helpers.peek.read_only(schema=schema, schemas={})


@pytest.mark.parametrize(
    "schema, expected_read_only",
    [({}, False), ({"readOnly": False}, False), ({"readOnly": True}, True)],
    ids=["missing", "false", "true"],
)
@pytest.mark.helper
def test_read_only(schema, expected_read_only):
    """
    GIVEN schema and expected readOnly
    WHEN read_only is called with the schema
    THEN the expected readOnly is returned.
    """

    returned_read_only = helpers.peek.read_only(schema=schema, schemas={})

    assert returned_read_only == expected_read_only


@pytest.mark.helper
def test_primary_key_wrong_type():
    """
    GIVEN schema with primary key defined as a string
    WHEN primary_key is called with the schema
    THEN MalformedSchemaError is raised.
    """
    schema = {"x-primary-key": "True"}

    with pytest.raises(exceptions.MalformedSchemaError):
        helpers.peek.primary_key(schema=schema, schemas={})


@pytest.mark.parametrize(
    "schema, expected_primary_key",
    [({}, False), ({"x-primary-key": False}, False), ({"x-primary-key": True}, True)],
    ids=["missing", "false", "true"],
)
@pytest.mark.helper
def test_primary_key(schema, expected_primary_key):
    """
    GIVEN schema and expected primary key
    WHEN primary_key is called with the schema
    THEN the expected primary key is returned.
    """
    returned_primary_key = helpers.peek.primary_key(schema=schema, schemas={})

    assert returned_primary_key == expected_primary_key


@pytest.mark.parametrize(
    "schema, schemas, expected_value",
    [
        ({}, {}, None),
        ({"key": "value 1"}, {}, "value 1"),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"key": "value 1"}},
            "value 1",
        ),
        ({"allOf": []}, {}, None),
        ({"allOf": [{"key": "value 1"}]}, {}, "value 1"),
        ({"allOf": [{}]}, {}, None),
        ({"allOf": [{"key": "value 1"}, {"key": "value 2"}]}, {}, "value 1"),
        ({"allOf": [{"key": "value 2"}, {"key": "value 1"}]}, {}, "value 2"),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"allOf": [{"key": "value 1"}]}},
            "value 1",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"allOf": [{"key": "value 1"}]}},
            "value 1",
        ),
    ],
    ids=[
        "missing",
        "plain",
        "$ref",
        "allOf empty",
        "allOf single no type",
        "allOf single",
        "allOf multiple first",
        "allOf multiple last",
        "$ref then allOf",
        "allOf with $ref",
    ],
)
@pytest.mark.helper
def test_peek_key(schema, schemas, expected_value):
    """
    GIVEN schema, schemas and expected value
    WHEN peek_key is called with the schema and schemas
    THEN the expected value is returned.
    """
    # pylint: disable=protected-access
    returned_type = helpers.peek.peek_key(schema=schema, schemas=schemas, key="key")

    assert returned_type == expected_value
