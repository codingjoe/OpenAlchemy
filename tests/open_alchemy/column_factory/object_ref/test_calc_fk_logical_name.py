"""Tests for calc_fk_logical_name."""
# pylint: disable=protected-access

import pytest

from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.column
@pytest.mark.object_ref
def test_calculate_fk_logical_name():
    """
    GIVEN artifacts with foreign key column name
    WHEN _calculate_fk_logical_name is called with the artifacts
    THEN a foreign key column is returned.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
    )

    name = object_ref._calc_fk_logical_name(
        artifacts=artifacts, logical_name="ref_schema"
    )

    assert name == "ref_schema_fk_column"
