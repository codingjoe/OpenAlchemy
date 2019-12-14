"""Gather artifacts for array reference."""

from open_alchemy import exceptions
from open_alchemy import helpers
from open_alchemy import types

from .. import object_ref


def gather_array_artifacts(
    *, schema: types.Schema, schemas: types.Schemas, logical_name: str
) -> types.ObjectArtifacts:
    """
    Gather artifacts required for array construction.

    Args:
        schema: The schema of the array reference.
        schemas: Used to resolve any $ref.

    Returns:
        The artifacts required to construct the array reference.

    """
    # Resolve any allOf and $ref
    schema = helpers.prepare_schema(schema=schema, schemas=schemas)

    # Get item specification
    item_schema = schema.get("items")
    if item_schema is None:
        raise exceptions.MalformedRelationshipError(
            "An array property must include items property."
        )
    return object_ref.gather_object_artifacts.gather_object_artifacts(
        schema=item_schema, logical_name=logical_name, schemas=schemas, required=None
    )
