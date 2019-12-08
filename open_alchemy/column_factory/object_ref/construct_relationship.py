"""Construct the relationship for the object reference."""

from sqlalchemy import orm

from open_alchemy import types


def construct_relationship(
    *, artifacts: types.ObjectArtifacts
) -> orm.RelationshipProperty:
    """
    Construct the relationship for the object reference.

    Args:
        artifacts: The artifacts for the object reference.

    Returns:
        The relationship for the object reference.

    """
    backref = None
    if artifacts.backref is not None:
        backref = orm.backref(artifacts.backref, uselist=artifacts.uselist)
    return orm.relationship(artifacts.ref_model_name, backref=backref)
