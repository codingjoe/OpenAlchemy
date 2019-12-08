"""Tests for _check_object_artifacts."""
# pylint: disable=protected-access

import pytest

from open_alchemy import exceptions
from open_alchemy import types
from open_alchemy.column_factory import object_ref


@pytest.mark.parametrize(
    "kwargs",
    [{"backref": None, "uselist": True}, {"secondary": "association"}],
    ids=["backref None uselist not None", "secondary not None"],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_check_object_artifacts_error(kwargs):
    """
    GIVEN kwargs for artifacts
    WHEN _check_object_artifacts is called with the artifacts
    THEN MalformedRelationshipError is raised.
    """
    artifacts = types.ObjectArtifacts(
        ref_model_name="RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
        **kwargs,
    )

    with pytest.raises(exceptions.MalformedRelationshipError):
        object_ref._check_object_artifacts(artifacts=artifacts)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"uselist": False},
        {"backref": "schema"},
        {"backref": "schema", "uselist": True},
    ],
    ids=[
        "model name only",
        "backref None uselist False",
        "backref not None",
        "backref with uselist",
    ],
)
@pytest.mark.column
@pytest.mark.object_ref
def test_check_object_artifacts(kwargs):
    """
    GIVEN kwargs for artifacts
    WHEN _check_object_artifacts is called with the artifacts
    THEN MalformedRelationshipError is not raised.
    """
    artifacts = types.ObjectArtifacts(
        ref_model_name="RefSchema",
        fk_column_name="fk_column",
        fk_column_artifacts=types.ColumnArtifacts("integer"),
        **kwargs,
    )

    object_ref._check_object_artifacts(artifacts=artifacts)
