"""Gather artifacts for constructing an object reference."""

import dataclasses
import typing

from open_alchemy import exceptions
from open_alchemy import helpers
from open_alchemy import types

from .calc_fk_artifacts import calc_fk_artifacts


def gather_object_artifacts(
    *,
    schema: types.Schema,
    logical_name: str,
    schemas: types.Schemas,
    required: typing.Optional[bool],
) -> types.ObjectArtifacts:
    """
    Gather artifacts for constructing an object reference.

    The schema must contain any of $ref and allOf. In the case of allOf, the array must
    contain exactly one $ref.

    Raises MalformedSchemaError if the schema does not include a $ref nor allOf with a
        $ref.

    Args:
        schema: The schema of the object reference.
        logical_name: The property name of the object reference.
        schemas: Used to resolve any $ref.
        required: Whether the relationship is a required property.

    Returns:
        The object artifacts required for construction.

    """
    intermediary_obj_artifacts = _handle_schema(
        logical_name=logical_name, schema=schema, schemas=schemas
    )

    fk_artifacts = calc_fk_artifacts(
        model_schema=intermediary_obj_artifacts.ref_schema,
        schemas=schemas,
        fk_column_name=intermediary_obj_artifacts.fk_column_name,
        required=required,
    )

    return types.ObjectArtifacts(
        ref_model_name=intermediary_obj_artifacts.ref_model_name,
        fk_column_name=intermediary_obj_artifacts.fk_column_name,
        fk_column_artifacts=fk_artifacts,
        backref=intermediary_obj_artifacts.backref,
        uselist=intermediary_obj_artifacts.uselist,
        secondary=intermediary_obj_artifacts.secondary,
    )


@dataclasses.dataclass
class _IntermediaryObjectArtifacts:
    """Object artifacts before foreign key column artifacts are gathered."""

    # The name of the referenced model
    ref_model_name: str
    # The name of the foreign key column
    fk_column_name: str
    # The schema for the foreign key column
    ref_schema: types.Schema
    # The back reference for the relationship
    backref: typing.Optional[str] = None
    # Whether to use a list for the back reference
    uselist: typing.Optional[bool] = None
    # The name of the secondary table to use for the relationship
    secondary: typing.Optional[str] = None


def _handle_schema(
    *, logical_name: str, schema: types.Schema, schemas: types.Schemas
) -> _IntermediaryObjectArtifacts:
    """
    Gather artifacts from the schema.

    Args:
        schema: The schema of the object reference.
        logical_name: The property name of the object reference.
        schemas: Used to resolve any $ref.

    Returns:
        The name of the referenced schema.

    """
    # Read $ref and allOf
    ref = schema.get("$ref")
    all_of = schema.get("allOf")

    if ref is not None:
        intermediary_obj_artifacts = _handle_ref(
            logical_name=logical_name, schema=schema, schemas=schemas
        )
    elif all_of is not None:
        intermediary_obj_artifacts = _handle_all_of(
            logical_name=logical_name, all_of_schema=all_of, schemas=schemas
        )
    else:
        raise exceptions.MalformedRelationshipError(
            "Relationships are defined using either $ref or allOf."
        )

    return intermediary_obj_artifacts


def _handle_ref(
    *, logical_name: str, schema: types.Schema, schemas: types.Schemas
) -> _IntermediaryObjectArtifacts:
    """
    Gather artifacts from a $ref.

    Args:
        schema: The schema of the object reference.
        logical_name: The property name of the object reference.
        schemas: Used to resolve any $ref.

    Returns:
        The name of the referenced schema.

    """
    ref_model_name, ref_schema = helpers.resolve_ref(
        name=logical_name, schema=schema, schemas=schemas
    )
    ref_schema = helpers.merge_all_of(schema=ref_schema, schemas=schemas)

    # Read other parameters
    backref = helpers.get_ext_prop(source=ref_schema, name="x-backref")
    uselist = helpers.get_ext_prop(source=ref_schema, name="x-uselist")
    secondary = helpers.get_ext_prop(source=ref_schema, name="x-secondary")
    fk_column_name = helpers.get_ext_prop(
        source=ref_schema, name="x-foreign-key-column"
    )
    if fk_column_name is None:
        fk_column_name = "id"

    return _IntermediaryObjectArtifacts(
        ref_model_name,
        fk_column_name,
        ref_schema,
        backref=backref,
        uselist=uselist,
        secondary=secondary,
    )


def _handle_all_of(
    *,
    logical_name: str,
    all_of_schema: typing.List[types.Schema],
    schemas: types.Schemas,
) -> _IntermediaryObjectArtifacts:
    """
    Gather artifacts from a allOf.

    Raise MalformedRelationshipError if there are no or multiple $ref in the allOf list.

    Args:
        schema: The schema of the object reference.
        logical_name: The property name of the object reference.
        schemas: Used to resolve any $ref.

    Returns:
        The name of the referenced schema.

    """
    # Initial values
    obj_artifacts: typing.Optional[_IntermediaryObjectArtifacts] = None
    secondary: typing.Optional[str] = None
    backref: typing.Optional[str] = None
    uselist: typing.Optional[bool] = None
    fk_column_name: typing.Optional[str] = None

    # Exceptions with their messages
    incorrect_number_of_ref = exceptions.MalformedRelationshipError(
        "Relationships defined with allOf must have exactly one $ref in the allOf "
        "list."
    )

    for sub_schema in all_of_schema:
        # Handle $ref
        if sub_schema.get("$ref") is not None:
            # Check whether $ref was already found
            if obj_artifacts is not None:
                raise incorrect_number_of_ref

            obj_artifacts = _handle_ref(
                logical_name=logical_name, schema=sub_schema, schemas=schemas
            )

        # Handle backref
        backref = _handle_key_single(
            key="x-backref",
            schema=sub_schema,
            default=backref,
            exception_message="Relationships may have at most 1 x-backref defined.",
        )
        # Handle uselist
        uselist = _handle_key_single(
            key="x-uselist",
            schema=sub_schema,
            default=uselist,
            exception_message="Relationships may have at most 1 x-uselist defined.",
        )
        # Handle secondary
        secondary = _handle_key_single(
            key="x-secondary",
            schema=sub_schema,
            default=secondary,
            exception_message="Relationships may have at most 1 x-secondary defined.",
        )
        # Handle fk_column_name
        fk_column_name = _handle_key_single(
            key="x-foreign-key-column",
            schema=sub_schema,
            default=fk_column_name,
            exception_message=(
                "Relationships may have at most 1 x-foreign-key-column defined."
            ),
        )

    # Check that $ref was found once
    if obj_artifacts is None:
        raise incorrect_number_of_ref
    if backref is not None:
        obj_artifacts.backref = backref
    if uselist is not None:
        obj_artifacts.uselist = uselist
    if secondary is not None:
        obj_artifacts.secondary = secondary
    if fk_column_name is not None:
        obj_artifacts.fk_column_name = fk_column_name

    return obj_artifacts


_TValue = typing.TypeVar("_TValue")


def _handle_key_single(
    *, key: str, schema: types.Schema, default: _TValue, exception_message: str
) -> _TValue:
    """
    Read value and enforce that it only exists once.

    Raise MalformedRelationshipError is default is not None and the key exists in the
        schema.

    ARgs:
        key: The key to read the value of.
        schema: The schema to read the value from.
        default: The default value to return.
        exception_message: The message raised with the exception.

    Returns:
        The value of the key or the default value,

    """
    sub_value = helpers.get_ext_prop(source=schema, name=key)
    if sub_value is not None:
        if default is not None:
            raise exceptions.MalformedRelationshipError(exception_message)

        return sub_value
    return default
