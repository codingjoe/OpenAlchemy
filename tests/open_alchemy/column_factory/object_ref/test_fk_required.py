"""Tests for _calculate_schema."""
# pylint: disable=protected-access

import pytest

from open_alchemy import exceptions
from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.parametrize(
    "model_schema",
    [
        {
            "properties": {
                "ref_table_fk_column": {"x-foreign-key": "ref_table.fk_column"}
            }
        },
        {
            "properties": {
                "ref_table_fk_column": {
                    "type": "not_fk_type",
                    "x-foreign-key": "ref_table.fk_column",
                }
            }
        },
        {"properties": {"ref_table_fk_column": {"type": "fk_type"}}},
        {
            "properties": {
                "ref_table_fk_column": {
                    "type": "fk_type",
                    "x-foreign-key": "wrong_table.wrong_column",
                }
            }
        },
    ],
    ids=["no type", "wrong type", "no x-foreign-key", "wrong x-foreign-key"],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_check_fk_required_invalid_schema(model_schema):
    """
    GIVEN model schema that is not valid
    WHEN check_fk_required is called
    THEN MalformedRelationshipError is raised.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts(
            "fk_type", foreign_key="ref_table.fk_column"
        ),
    )
    fk_logical_name = "ref_table_fk_column"

    with pytest.raises(exceptions.MalformedRelationshipError):
        object_ref.check_fk_required(
            artifacts=artifacts,
            fk_logical_name=fk_logical_name,
            model_schema=model_schema,
            schemas={},
        )


@pytest.mark.parametrize(
    "model_schema, schemas, expected_required",
    [
        ({"properties": {}}, {}, True),
        (
            {
                "properties": {
                    "ref_table_fk_column": {
                        "type": "fk_type",
                        "x-foreign-key": "ref_table.fk_column",
                    }
                }
            },
            {},
            False,
        ),
        (
            {
                "properties": {
                    "ref_table_fk_column": {"$ref": "#/components/schemas/FkSchema"}
                }
            },
            {"FkSchema": {"type": "fk_type", "x-foreign-key": "ref_table.fk_column"}},
            False,
        ),
        (
            {
                "properties": {
                    "ref_table_fk_column": {
                        "allOf": [
                            {"type": "fk_type", "x-foreign-key": "ref_table.fk_column"}
                        ]
                    }
                }
            },
            {},
            False,
        ),
    ],
    ids=[
        "not in model schema",
        "in model schema",
        "in model schema $ref",
        "in model schema allOf",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_check_fk_required(model_schema, schemas, expected_required):
    """
    GIVEN foreign key spec, foreign key logical name, model schema, schemas and
        expected required
    WHEN check_fk_required is called
    THEN the expected required is returned.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts(
            "fk_type", foreign_key="ref_table.fk_column"
        ),
    )
    fk_logical_name = "ref_table_fk_column"

    required = object_ref.check_fk_required(
        artifacts=artifacts,
        fk_logical_name=fk_logical_name,
        model_schema=model_schema,
        schemas=schemas,
    )

    assert required == expected_required
