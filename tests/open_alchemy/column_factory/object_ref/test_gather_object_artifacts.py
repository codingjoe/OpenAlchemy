"""Tests for the column factory."""
# pylint: disable=protected-access

import pytest

from open_alchemy import exceptions
from open_alchemy.column_factory import object_ref


@pytest.mark.parametrize(
    "schemas",
    [
        {
            "RefSchema": {
                "x-tablename": "ref_schema",
                "properties": {"id": {"type": "integer"}},
            }
        },
        {
            "RefSchema": {
                "type": "notObject",
                "x-tablename": "ref_schema",
                "properties": {"id": {"type": "integer"}},
            }
        },
    ],
    ids=["no type", "not object type"],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_ref_error(schemas):
    """
    GIVEN referenced schema that is not valid and schema
    WHEN _handle_schema is called with the schema and schemas
    THEN MalformedRelationshipError is raised.
    """
    schema = {"$ref": "#/components/schemas/RefSchema"}

    with pytest.raises(exceptions.MalformedRelationshipError):
        object_ref.gather_object_artifacts._handle_schema(
            logical_name="", schema=schema, schemas=schemas
        )


@pytest.mark.parametrize(
    "schema",
    [
        [{"type": "object"}],
        [
            {"$ref": "#/components/schemas/Schema1"},
            {"$ref": "#/components/schemas/Schema2"},
        ],
        [
            {"$ref": "#/components/schemas/Schema1"},
            {"x-backref": "backSchema1"},
            {"x-backref": "backSchema2"},
        ],
        [
            {"$ref": "#/components/schemas/Schema1"},
            {"x-secondary": "secondary 1"},
            {"x-secondary": "secondary 2"},
        ],
        [
            {"$ref": "#/components/schemas/Schema1"},
            {"x-foreign-key-column": "column 1"},
            {"x-foreign-key-column": "column 2"},
        ],
        [
            {"$ref": "#/components/schemas/Schema1"},
            {"x-uselist": True},
            {"x-uselist": False},
        ],
    ],
    ids=[
        "object",
        "multiple ref",
        "multiple x-backref",
        "multiple x-secondary",
        "multiple x-foreign-key-column",
        "multiple x-uselist",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_all_of_error(schema):
    """
    GIVEN schema
    WHEN _handle_schema is called with the schema
    THEN MalformedRelationshipError is raised.
    """
    schema = {"allOf": schema}
    schemas = {"Schema1": {"type": "object"}, "Schema2": {"type": "object"}}

    with pytest.raises(exceptions.MalformedRelationshipError):
        object_ref.gather_object_artifacts._handle_schema(
            logical_name="", schema=schema, schemas=schemas
        )


@pytest.mark.parametrize(
    "schema, schemas",
    [
        ({"$ref": "#/components/schemas/RefSchema"}, {"RefSchema": {"type": "object"}}),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object"}},
        ),
    ],
    ids=["$ref", "allOf"],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_ref_model_name(schema, schemas):
    """
    GIVEN specification and schemas
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the referenced schema name is returned as the ref logical name.
    """
    obj_artifacts = object_ref.gather_object_artifacts._handle_schema(
        schema=schema, logical_name="", schemas=schemas
    )

    assert obj_artifacts.ref_model_name == "RefSchema"


@pytest.mark.parametrize(
    "schema, schemas",
    [
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {
                "RefSchema": {
                    "type": "object",
                    "x-tablename": "table 1",
                    "properties": {"id": {"type": "fkType"}, "fk": {"type": "fkType"}},
                }
            },
        ),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {
                "RefSchema": {
                    "allOf": [
                        {
                            "type": "object",
                            "x-tablename": "table 1",
                            "properties": {
                                "id": {"type": "fkType"},
                                "fk": {"type": "fkType"},
                            },
                        }
                    ]
                }
            },
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {
                "RefSchema": {
                    "type": "object",
                    "x-tablename": "table 1",
                    "properties": {"id": {"type": "fkType"}, "fk": {"type": "fkType"}},
                }
            },
        ),
    ],
    ids=["$ref", "$ref to allOf", "allOf"],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_fk_artifacts(schema, schemas):
    """
    GIVEN specification and schemas
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the expected foreign key artifacts.
    """
    obj_artifacts = object_ref.gather_object_artifacts.gather_object_artifacts(
        schema=schema, logical_name="", schemas=schemas, required=False
    )

    assert obj_artifacts.fk_column_artifacts.type == "fkType"
    assert obj_artifacts.fk_column_artifacts.foreign_key == "table 1.id"


@pytest.mark.parametrize(
    "schema, schemas, expected_backref",
    [
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object", "x-backref": "backref 1"}},
            "backref 1",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "backref 2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2"},
                    {"x-uselist": False},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "backref 2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-uselist": False},
                    {"x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "backref 2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2", "x-uselist": False},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "backref 2",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object", "x-backref": "backref 1"}},
            "backref 1",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object", "x-backref": "backref 1"}},
            "backref 2",
        ),
    ],
    ids=[
        "$ref no backref",
        "$ref backref",
        "allOf no backref",
        "allOf backref",
        "allOf backref before other",
        "allOf backref after other",
        "allOf backref with uselist",
        "allOf $ref backref",
        "allOf backref $ref backref",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_backref(schema, schemas, expected_backref):
    """
    GIVEN specification and schemas and expected backref
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the expected backref is returned.
    """
    obj_artifacts = object_ref.gather_object_artifacts._handle_schema(
        schema=schema, logical_name="", schemas=schemas
    )

    assert obj_artifacts.backref == expected_backref


@pytest.mark.parametrize(
    "schema, schemas, expected_uselist",
    [
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {
                "RefSchema": {
                    "type": "object",
                    "x-backref": "backref 1",
                    "x-uselist": True,
                }
            },
            True,
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-uselist": False},
                    {"x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            False,
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-uselist": False, "x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            False,
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {
                "RefSchema": {
                    "type": "object",
                    "x-backref": "backref 1",
                    "x-uselist": True,
                }
            },
            True,
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2"},
                    {"x-uselist": False},
                ]
            },
            {
                "RefSchema": {
                    "type": "object",
                    "x-backref": "backref 1",
                    "x-uselist": True,
                }
            },
            False,
        ),
    ],
    ids=[
        "$ref no uselist",
        "$ref uselist",
        "allOf no uselist",
        "allOf uselist",
        "allOf uselist with backref",
        "allOf $ref uselist",
        "allOf uselist $ref uselist",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_uselist(schema, schemas, expected_uselist):
    """
    GIVEN specification and schemas and expected uselist
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the expected uselist is returned.
    """
    obj_artifacts = object_ref.gather_object_artifacts._handle_schema(
        schema=schema, logical_name="", schemas=schemas
    )

    assert obj_artifacts.uselist == expected_uselist


@pytest.mark.parametrize(
    "schema, schemas, expected_secondary",
    [
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object", "x-secondary": "secondary 1"}},
            "secondary 1",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object"}},
            None,
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-secondary": "secondary 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "secondary 2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-secondary": "secondary 2"},
                    {"x-backref": "backref 1"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "secondary 2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 1"},
                    {"x-secondary": "secondary 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "secondary 2",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object", "x-secondary": "secondary 1"}},
            "secondary 1",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-secondary": "secondary 2"},
                ]
            },
            {"RefSchema": {"type": "object", "x-secondary": "secondary 1"}},
            "secondary 2",
        ),
    ],
    ids=[
        "$ref no secondary",
        "$ref secondary",
        "allOf no secondary",
        "allOf secondary",
        "allOf secondary before other",
        "allOf secondary after other",
        "allOf $ref secondary",
        "allOf secondary $ref secondary",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_secondary(schema, schemas, expected_secondary):
    """
    GIVEN specification and schemas and expected secondary
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the expected secondary is returned.
    """
    obj_artifacts = object_ref.gather_object_artifacts._handle_schema(
        schema=schema, logical_name="", schemas=schemas
    )

    assert obj_artifacts.secondary == expected_secondary


@pytest.mark.parametrize(
    "schema, schemas, expected_fk_column_name",
    [
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object"}},
            "id",
        ),
        (
            {"$ref": "#/components/schemas/RefSchema"},
            {"RefSchema": {"type": "object", "x-foreign-key-column": "fk_column_1"}},
            "fk_column_1",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object"}},
            "id",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-foreign-key-column": "fk_column_2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "fk_column_2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-foreign-key-column": "fk_column_2"},
                    {"x-backref": "backref 2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "fk_column_2",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-backref": "backref 2"},
                    {"x-foreign-key-column": "fk_column_2"},
                ]
            },
            {"RefSchema": {"type": "object"}},
            "fk_column_2",
        ),
        (
            {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            {"RefSchema": {"type": "object", "x-foreign-key-column": "fk_column_1"}},
            "fk_column_1",
        ),
        (
            {
                "allOf": [
                    {"$ref": "#/components/schemas/RefSchema"},
                    {"x-foreign-key-column": "fk_column_2"},
                ]
            },
            {"RefSchema": {"type": "object", "x-foreign-key-column": "fk_column_1"}},
            "fk_column_2",
        ),
    ],
    ids=[
        "$ref no fk",
        "$ref fk",
        "allOf no fk",
        "allOf fk",
        "allOf fk before other",
        "allOf fk after other",
        "allOf $ref fk",
        "allOf fk $ref fk",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_fk_column_name(schema, schemas, expected_fk_column_name):
    """
    GIVEN specification and schemas and expected foreign key column
    WHEN gather_object_artifacts is called with the specification and schemas
    THEN the expected foreign key column is returned.
    """
    obj_artifacts = object_ref.gather_object_artifacts._handle_schema(
        schema=schema, logical_name="", schemas=schemas
    )

    assert obj_artifacts.fk_column_name == expected_fk_column_name
