"""Tests for _construct_fk_column."""
# pylint: disable=protected-access

import pytest
import sqlalchemy

from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.column
@pytest.mark.object_ref
def test_construct_fk_column():
    """
    GIVEN artifacts with foreign key column artifacts
    WHEN _construct_fk_column is called with the artifacts
    THEN a foreign key column is returned.
    """
    fk_column_artifacts = types.ColumnArtifacts("integer", foreign_key="table.column")
    artifacts = types.ObjectArtifacts(
        "RefSchema", fk_column_name="fk_column", fk_column_artifacts=fk_column_artifacts
    )

    column = object_ref._construct_fk_column(artifacts=artifacts)

    assert isinstance(column.type, sqlalchemy.Integer)
    assert len(column.foreign_keys) == 1
    foreign_key = column.foreign_keys.pop()
    assert str(foreign_key) == "ForeignKey('table.column')"
