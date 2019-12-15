"""Tests for checking array artifacts."""
# pylint: disable=protected-access

import pytest

from open_alchemy import exceptions
from open_alchemy import types
from open_alchemy.column_factory import array_ref


@pytest.mark.column
@pytest.mark.array_ref
def test_error():
    """
    GIVEN artifacts with uselist set
    WHEN _check_array_artifacts is called with the artifacts
    THEN MalformedRelationshipError is raised.
    """
    artifacts = types.ObjectArtifacts(None, None, None, uselist=True)

    with pytest.raises(exceptions.MalformedRelationshipError):
        array_ref._check_array_artifacts(artifacts=artifacts)


@pytest.mark.column
@pytest.mark.array_ref
def test_success():
    """
    GIVEN valid artifacts
    WHEN _check_array_artifacts is called with the artifacts
    THEN MalformedRelationshipError is not raised.
    """
    artifacts = types.ObjectArtifacts(None, None, None)

    array_ref._check_array_artifacts(artifacts=artifacts)
