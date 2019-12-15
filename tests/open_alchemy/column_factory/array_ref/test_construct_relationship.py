"""Tests for _construct_relationship."""
# pylint: disable=protected-access

import pytest

from open_alchemy import types
from open_alchemy.column_factory import array_ref


@pytest.mark.parametrize(
    "kwargs, expected_backref, expected_secondary",
    [
        ({}, None, None),
        ({"backref": "schema"}, "schema", None),
        ({"secondary": "association"}, None, "association"),
    ],
    ids=["plain", "backref", "secondary"],
)
@pytest.mark.column
@pytest.mark.array_ref
def test_construct_relationship(kwargs, expected_backref, expected_secondary):
    """
    GIVEN kwargs for artifacts and expected backref and secondary
    WHEN _construct_relationship is called with the artifacts
    THEN a relationship referring to the referenced model and with the expected backref
        and secondary is constructed.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
        **kwargs,
    )

    relationship = array_ref._construct_relationship(artifacts=artifacts)

    assert relationship.argument == "RefSchema"
    assert relationship.backref == expected_backref
    assert relationship.secondary == expected_secondary
