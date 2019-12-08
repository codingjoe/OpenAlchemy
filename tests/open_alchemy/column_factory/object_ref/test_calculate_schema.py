"""Tests for _calculate_schema."""
# pylint: disable=protected-access

import pytest

from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.column
@pytest.mark.object_ref
def test_calculate_schema():
    """
    GIVEN object artifacts
    WHEN _calculate_schema is called with the artifacts
    THEN the schema for the object reference is returned.
    """
    artifacts = types.ObjectArtifacts(
        ref_model_name="RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )

    schema = object_ref._calculate_schema(artifacts=artifacts)

    assert schema == {"type": "object", "x-de-$ref": "RefSchema"}
