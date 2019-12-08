"""Tests for _construct_relationship."""
# pylint: disable=protected-access

import pytest

from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.parametrize(
    "kwargs, expected_backref, expected_uselist",
    [
        ({}, None, None),
        ({"backref": "schema"}, "schema", None),
        ({"uselist": True}, None, None),
        ({"backref": "schema", "uselist": False}, "schema", False),
        ({"backref": "schema", "uselist": True}, "schema", True),
    ],
    ids=[
        "plain",
        "backref",
        "uselist",
        "backref and uselist false",
        "backref and uselist true",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_construct_relationship(kwargs, expected_backref, expected_uselist):
    """
    GIVEN kwargs for artifacts and expected backref and uselist
    WHEN _construct_relationship is called with the artifacts
    THEN a relationship referring to the referenced model and with the expected backref
        and uselist is constructed.
    """
    artifacts = types.ObjectArtifacts(
        "RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
        **kwargs,
    )

    relationship = object_ref._construct_relationship(artifacts=artifacts)

    assert relationship.argument == "RefSchema"
    if expected_backref is None:
        assert relationship.backref is None
    else:
        backref, kwargs = relationship.backref
        assert backref == expected_backref
        assert kwargs["uselist"] == expected_uselist
