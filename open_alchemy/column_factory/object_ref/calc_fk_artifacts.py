"""Calculate the foreign key column artifacts."""

import typing

from open_alchemy import exceptions
from open_alchemy import helpers
from open_alchemy import types
from open_alchemy.column_factory import column


def calc_fk_artifacts(
    *,
    model_schema: types.Schema,
    schemas: types.Schemas,
    fk_column_name: str,
    required: typing.Optional[bool],
) -> types.ColumnArtifacts:
    """
    Calculate the foreign key column artifacts.

    Args:
        model_schema: The schema of the model.
        schemas: Used to resolve any $ref.
        fk_column_name: The name of the foreign key column.
        required: Whether the foreign key is required.

    Returns:
        The artifacts for the foreign key column.

    """
    tablename = helpers.get_ext_prop(source=model_schema, name="x-tablename")
    if not tablename:
        raise exceptions.MalformedRelationshipError(
            "Referenced object is missing x-tablename property."
        )
    properties = model_schema.get("properties")
    if properties is None:
        raise exceptions.MalformedRelationshipError(
            "Referenced object does not have any properties."
        )
    fk_schema = properties.get(fk_column_name)
    if fk_schema is None:
        raise exceptions.MalformedRelationshipError(
            f"Referenced object does not have {fk_column_name} property."
        )
    # Preparing schema
    prepared_fk_schema = helpers.prepare_schema(schema=fk_schema, schemas=schemas)
    fk_type = prepared_fk_schema.get("type")
    if fk_type is None:
        raise exceptions.MalformedRelationshipError(
            f"Referenced object {fk_column_name} property does not have a type."
        )

    nullable = helpers.peek.nullable(schema=prepared_fk_schema, schemas=schemas)
    nullable = column.calculate_nullable(nullable=nullable, required=required)

    return types.ColumnArtifacts(
        fk_type, foreign_key=f"{tablename}.{fk_column_name}", nullable=nullable
    )
