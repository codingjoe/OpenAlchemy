"""Construct the foreign key column for the relationship."""

import sqlalchemy

from open_alchemy import types

from .. import column


def construct_fk_column(*, artifacts: types.ObjectArtifacts) -> sqlalchemy.Column:
    """
    Construct the foreign key column for the relationship.

    Raises MissingArgumentError if the foreign key column artifacts are None.

    Args:
        artifacts: Used to construct the foreign key column.

    Returns:
        The foreign key column.

    """
    return column.construct_column(artifacts=artifacts.fk_column_artifacts)
