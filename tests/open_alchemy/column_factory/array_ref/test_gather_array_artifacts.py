"""Tests for gathering array artifacts."""

import pytest

from open_alchemy import exceptions
from open_alchemy.column_factory import array_ref


@pytest.mark.parametrize(
    "schema, schemas",
    [
        ({"type": "array"}, {}),
        ({"type": "array", "items": {}}, {}),
        ({"type": "array", "items": {"allOf": []}}, {}),
        (
            {
                "type": "array",
                "items": {
                    "allOf": [
                        {"$ref": "#/components/schemas/RefSchema1"},
                        {"$ref": "#/components/schemas/RefSchema2"},
                    ]
                },
            },
            {"RefSchema1": {}, "RefSchema2": {}},
        ),
        (
            {"type": "array", "items": {"$ref": "#/components/schemas/RefSchema"}},
            {
                "RefSchema": {
                    "x-tablename": "ref_schema",
                    "properties": {"id": {"type": "integer"}},
                }
            },
        ),
        (
            {
                "type": "array",
                "items": {"allOf": [{"$ref": "#/components/schemas/RefSchema"}]},
            },
            {"RefSchema": {}},
        ),
        (
            {"type": "array", "items": {"$ref": "#/components/schemas/RefSchema"}},
            {"RefSchema": {"type": "integer"}},
        ),
        (
            {"type": "array", "items": {"$ref": "#/components/schemas/RefSchema"}},
            {"RefSchema": {"type": "object"}},
        ),
    ],
    ids=[
        "no items",
        "items without $ref and allOf",
        "items allOf without $ref",
        "items allOf multiple $ref",
        "$ref items no type",
        "allOf items no type",
        "items type not object",
        "items no x-tablename",
    ],
)
@pytest.mark.column
@pytest.mark.array_ref
def test_handle_array_invalid(schema, schemas):
    """
    GIVEN array schema that is not valid and schemas
    WHEN gather_array_artifacts is called
    THEN MalformedRelationshipError is raised.
    """
    with pytest.raises(exceptions.MalformedRelationshipError):
        array_ref.gather_array_artifacts(
            schema=schema, schemas=schemas, logical_name=""
        )
