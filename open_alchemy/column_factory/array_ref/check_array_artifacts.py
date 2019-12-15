"""Check array artifacts."""

from open_alchemy import exceptions
from open_alchemy import types


def check_array_artifacts(*, artifacts: types.ObjectArtifacts) -> None:
    """
    Check that array artifacts are valid for an array reference.

    Raise MalformedRelationshipError is uselist is defined.

    Args:
        artifacts: The artifacts to check.

    """
    if artifacts.uselist is not None:
        raise exceptions.MalformedRelationshipError(
            "x-uselist is not supported for relationships with arrays."
        )
