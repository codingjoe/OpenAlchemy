"""Tests for _calculate_schema."""
# pylint: disable=protected-access

import pytest

from open_alchemy import types
from open_alchemy.column_factory import array_ref


@pytest.mark.column
@pytest.mark.array_ref
def test_calculate_schema():
    """
    GIVEN array artifacts
    WHEN _calculate_schema is called with the artifacts
    THEN the schema for the array reference is returned.
    """
    artifacts = types.ObjectArtifacts(
        ref_model_name="RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )

    schema = array_ref._calculate_schema(artifacts=artifacts)

    assert schema == {
        "type": "array",
        "items": {"type": "object", "x-de-$ref": "RefSchema"},
    }
