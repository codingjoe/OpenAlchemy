"""Set the foreign key on an existing model or add it to the schemas."""

from open_alchemy import exceptions
from open_alchemy import facades
from open_alchemy import helpers
from open_alchemy import types

from ...utility_base import TOptUtilityBase
from .. import column
from .. import object_ref


def set_foreign_key(
    *,
    artifacts: types.ObjectArtifacts,
    model_schema: types.Schema,
    schemas: types.Schemas,
) -> None:
    """
    Set the foreign key on an existing model or add it to the schemas.

    Args:
        artifacts: The artifacts for constructing the array reference.
        model_schema: The schema of the one to many parent.
        schemas: All the model schemas.

    """
    # Check that model is in schemas
    if artifacts.ref_model_name not in schemas:
        raise exceptions.MalformedRelationshipError(
            f"{artifacts.ref_model_name} referenced in relationship was not found in "
            "the schemas."
        )

    # Calculate foreign key specification
    fk_spec = object_ref.handle_object_reference(
        spec=model_schema, schemas=schemas, fk_column=artifacts.fk_column_name
    )

    # Calculate values for foreign key
    tablename = helpers.get_ext_prop(source=model_schema, name="x-tablename")
    fk_logical_name = f"{tablename}_{artifacts.fk_column_name}"

    # Gather referenced schema
    ref_schema = schemas[artifacts.ref_model_name]
    # Any top level $ref must already be resolved
    ref_schema = helpers.merge_all_of(schema=ref_schema, schemas=schemas)
    fk_required = object_ref.check_foreign_key_required_spec(
        fk_spec=fk_spec,
        fk_logical_name=fk_logical_name,
        model_schema=ref_schema,
        schemas=schemas,
    )
    if not fk_required:
        return

    # Handle model already constructed
    ref_model: TOptUtilityBase = facades.models.get_model(name=artifacts.ref_model_name)
    if ref_model is not None:
        # Construct foreign key
        _, fk_column = column.handle_column(schema=fk_spec)
        setattr(ref_model, fk_logical_name, fk_column)
        return

    # Handle model not constructed
    schemas[artifacts.ref_model_name] = {
        "allOf": [
            schemas[artifacts.ref_model_name],
            {
                "type": "object",
                "properties": {fk_logical_name: {**fk_spec, "x-dict-ignore": True}},
            },
        ]
    }
