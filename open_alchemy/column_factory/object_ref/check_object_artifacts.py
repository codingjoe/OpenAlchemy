"""Check whether object artifacts are valid for object references."""

from open_alchemy import exceptions
from open_alchemy import types


def check_object_artifacts(*, artifacts: types.ObjectArtifacts) -> None:
    """
    Check whether object artifacts are valid for object references.

    Raises MalformedRelationshipError if uselist is not None and backref is None.
    Raises MalformedRelationshipError if secondary is not None.

    Args:
        artifacts: The artifacts to check.

    """
    if artifacts.backref is None and artifacts.uselist is True:
        raise exceptions.MalformedRelationshipError(
            "Uselist is only valid for an object reference with a back reference."
        )
    if artifacts.secondary is not None:
        raise exceptions.MalformedRelationshipError(
            "A secondary table is only valid for a many to many relationship."
        )
