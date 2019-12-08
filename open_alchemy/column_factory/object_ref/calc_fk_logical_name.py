"""Calculate the foreign key column logical name."""

from open_alchemy import types


def calc_fk_logical_name(*, artifacts: types.ObjectArtifacts, logical_name: str) -> str:
    """
    Calculate the foreign key column logical name.

    Raises MissingArgumentError if the foreign key column artifacts are None.

    Args:
        artifacts: The artifacts for the object reference.
        logical_name: The logical name of the relationship.

    Returns:
        The logical name for the foreign key column.

    """
    return f"{logical_name}_{artifacts.fk_column_name}"
