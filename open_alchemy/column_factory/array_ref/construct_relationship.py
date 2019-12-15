"""Construct the relationship for the array reference."""

from sqlalchemy import orm

from open_alchemy import types


def construct_relationship(
    *, artifacts: types.ObjectArtifacts
) -> orm.RelationshipProperty:
    """
    Construct the relationship for the array reference.

    Args:
        artifacts: The artifacts for the array reference.

    Returns:
        The relationship for the array reference.

    """
    return orm.relationship(
        artifacts.ref_model_name,
        backref=artifacts.backref,
        secondary=artifacts.secondary,
    )
