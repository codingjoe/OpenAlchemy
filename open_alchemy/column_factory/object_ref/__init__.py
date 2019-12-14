"""Functions relating to object references."""
# pylint: disable=useless-import-alias

import dataclasses
import typing

import sqlalchemy
from sqlalchemy import orm

from open_alchemy import exceptions
from open_alchemy import helpers
from open_alchemy import types

from .. import column
from . import gather_object_artifacts as gather_object_artifacts
from .calc_fk_artifacts import calc_fk_artifacts as _calc_fk_artifacts
from .calc_fk_logical_name import calc_fk_logical_name as _calc_fk_logical_name
from .calculate_schema import calculate_schema as _calculate_schema
from .check_fk_required import check_fk_required as check_fk_required
from .check_object_artifacts import check_object_artifacts as _check_object_artifacts
from .construct_fk_column import construct_fk_column as _construct_fk_column
from .construct_relationship import construct_relationship as _construct_relationship


def handle_object(
    *,
    spec: types.Schema,
    schemas: types.Schemas,
    required: typing.Optional[bool] = None,
    logical_name: str,
    model_schema: types.Schema,
) -> typing.Tuple[
    typing.List[
        typing.Tuple[str, typing.Union[sqlalchemy.Column, orm.RelationshipProperty]]
    ],
    typing.Any,
]:
    """
    Generate properties for a reference to another object.

    Assume that, when any $ref and allOf are resolved, the schema is an object.

    Args:
        spec: The schema for the column.
        schemas: Used to resolve any $ref.
        required: Whether the object property is required.
        logical_name: The logical name in the specification for the schema.
        model_schema: The schema of the model.

    Returns:
        The logical name, the SQLAlchemy column for the foreign key and the logical
        name and relationship for the reference to the object and the specification to
        record for the object reference.

    """
    # Retrieve artifacts required for object
    artifacts = gather_object_artifacts.gather_object_artifacts(
        schema=spec, logical_name=logical_name, schemas=schemas, required=required
    )

    # Check artifacts
    _check_object_artifacts(artifacts=artifacts)

    # Construct foreign key
    fk_logical_name = _calc_fk_logical_name(
        artifacts=artifacts, logical_name=logical_name
    )
    fk_required = check_fk_required(
        artifacts=artifacts,
        fk_logical_name=fk_logical_name,
        model_schema=model_schema,
        schemas=schemas,
    )
    if fk_required:
        fk_column = _construct_fk_column(artifacts=artifacts)
        return_value = [(fk_logical_name, fk_column)]
    else:
        return_value = []

    # Creating relationship
    relationship = _construct_relationship(artifacts=artifacts)
    return_value.append((logical_name, relationship))

    # Calculate schema
    return_schema = _calculate_schema(artifacts=artifacts)
    return return_value, return_schema


@dataclasses.dataclass
class ObjectArtifacts:
    """Artifacts retrieved from object schema."""

    spec: types.Schema
    ref_logical_name: str
    backref: typing.Optional[str]
    fk_column: str
    uselist: typing.Optional[bool]
    secondary: typing.Optional[str]


def gather_object_artifacts_old(
    *, spec: types.Schema, logical_name: str, schemas: types.Schemas
) -> ObjectArtifacts:
    """
    Collect artifacts from a specification for constructing an object reference.

    Get the prepared specification, reference logical name, back reference and foreign
    key column name from a raw object specification.

    Raise MalformedRelationshipError if neither $ref nor $allOf is found.
    Raise MalformedRelationshipError if uselist is defined but backref is not.
    Raise MalformedRelationshipError if multiple $ref, x-backref, x-secondary,
    x-foreign-key-column or x-uselist are found.

    Args:
        spec: The schema for the column.
        schemas: Used to resolve any $ref.
        logical_name: The logical name in the specification for the schema.

    Returns:
        The prepared specification, reference logical name, back reference and foreign
        key column.

    """
    # Default backref
    backref = None
    # Default uselist
    uselist = None
    # Default secondary
    secondary = None
    # Initial foreign key column
    fk_column = None

    # Checking for $ref and allOf
    ref = spec.get("$ref")
    all_of = spec.get("allOf")

    if ref is not None:
        # Handle $ref
        ref_logical_name, spec = helpers.resolve_ref(
            name=logical_name, schema=spec, schemas=schemas
        )
    elif all_of is not None:
        # Checking for $ref, and x-backref and x-foreign-key-column counts
        _check_object_all_of(all_of_spec=all_of)

        # Handle allOf
        for sub_spec in all_of:
            backref = helpers.get_ext_prop(
                source=sub_spec, name="x-backref", default=backref
            )
            uselist = helpers.get_ext_prop(
                source=sub_spec, name="x-uselist", default=uselist
            )
            secondary = helpers.get_ext_prop(
                source=sub_spec, name="x-secondary", default=secondary
            )
            fk_column = helpers.get_ext_prop(
                source=sub_spec, name="x-foreign-key-column", default=fk_column
            )
            if sub_spec.get("$ref") is not None:
                ref_logical_name, spec = helpers.resolve_ref(
                    name=logical_name, schema=sub_spec, schemas=schemas
                )
    else:
        raise exceptions.MalformedRelationshipError(
            "Relationships are defined using either $ref or allOf."
        )

    # Resolving allOf
    spec = helpers.merge_all_of(schema=spec, schemas=schemas)

    # If backref has not been found look in referenced schema
    if backref is None:
        backref = helpers.get_ext_prop(source=spec, name="x-backref")
    # If uselist has not been found look in referenced schema
    if uselist is None:
        uselist = helpers.get_ext_prop(source=spec, name="x-uselist")
    # If secondary has not been found look in referenced schema
    if secondary is None:
        secondary = helpers.get_ext_prop(source=spec, name="x-secondary")
    # If foreign key column has not been found look in referenced schema
    if fk_column is None:
        fk_column = helpers.get_ext_prop(source=spec, name="x-foreign-key-column")
    # If foreign key column is still None, default to id
    if fk_column is None:
        fk_column = "id"

    # Check if uselist is defined and backref is not
    if uselist is not None and backref is None:
        raise exceptions.MalformedRelationshipError(
            "Relationships with x-uselist defined must also define x-backref."
        )

    return ObjectArtifacts(
        spec, ref_logical_name, backref, fk_column, uselist, secondary
    )


def _check_object_all_of(*, all_of_spec: types.AllOfSpec) -> None:
    """
    Check format of allOf for an object reference.

    Raise MalformedRelationshipError if the allOf schema is not as expected.

    Args:
        all_of_spec: The allOf specification to check.

    """
    # Checking for $ref and x-backref counts
    ref_count = 0
    backref_count = 0
    fk_column_count = 0
    uselist_count = 0
    secondary_count = 0
    for sub_spec in all_of_spec:
        if sub_spec.get("$ref") is not None:
            ref_count += 1
        if sub_spec.get("x-backref") is not None:
            backref_count += 1
        if sub_spec.get("x-foreign-key-column") is not None:
            fk_column_count += 1
        if sub_spec.get("x-uselist") is not None:
            uselist_count += 1
        if sub_spec.get("x-secondary") is not None:
            secondary_count += 1
    if ref_count != 1:
        raise exceptions.MalformedRelationshipError(
            "Relationships defined with allOf must have exactly one $ref in the allOf "
            "list."
        )
    if backref_count > 1:
        raise exceptions.MalformedRelationshipError(
            "Relationships may have at most 1 x-backref defined."
        )
    if fk_column_count > 1:
        raise exceptions.MalformedRelationshipError(
            "Relationships may have at most 1 x-foreign-key-column defined."
        )
    if uselist_count > 1:
        raise exceptions.MalformedRelationshipError(
            "Relationships may have at most 1 x-uselist defined."
        )
    if secondary_count > 1:
        raise exceptions.MalformedRelationshipError(
            "Relationships may have at most 1 x-secondary defined."
        )


def handle_object_reference(
    *, spec: types.Schema, schemas: types.Schemas, fk_column: str
) -> types.Schema:
    """
    Determine the foreign key schema for an object reference.

    Args:
        spec: The schema of the object reference.
        schemas: All defined schemas.
        fk_column: The foreign column name to use.

    Returns:
        The foreign key schema.

    """
    tablename = helpers.get_ext_prop(source=spec, name="x-tablename")
    if not tablename:
        raise exceptions.MalformedSchemaError(
            "Referenced object is missing x-tablename property."
        )
    properties = spec.get("properties")
    if properties is None:
        raise exceptions.MalformedSchemaError(
            "Referenced object does not have any properties."
        )
    fk_logical_name = fk_column if fk_column is not None else "id"
    fk_spec = properties.get(fk_logical_name)
    if fk_spec is None:
        raise exceptions.MalformedSchemaError(
            f"Referenced object does not have {fk_logical_name} property."
        )
    # Preparing specification
    prepared_fk_spec = helpers.prepare_schema(schema=fk_spec, schemas=schemas)
    fk_type = prepared_fk_spec.get("type")
    if fk_type is None:
        raise exceptions.MalformedSchemaError(
            f"Referenced object {fk_logical_name} property does not have a type."
        )

    return {"type": fk_type, "x-foreign-key": f"{tablename}.{fk_logical_name}"}


def check_foreign_key_required_spec(
    *,
    fk_spec: types.Schema,
    fk_logical_name: str,
    model_schema: types.Schema,
    schemas: types.Schemas,
) -> bool:
    """
    Check whether a foreign key has already been defined.

    Assume model_schema has already resolved any $ref and allOf at the object level.
    They may not have been resolved at the property level.

    Check whether the proposed logical name is already defined on the model schema. If
    it has been, check that the type is correct and that the foreign key reference has
    been defined and points to the correct column.

    Raise MalformedRelationshipError if a property has already been defined with the
    same name as is proposed for the foreign key but it has the wrong type or does not
    define the correct foreign key constraint.

    Args:
        fk_spec: The proposed foreign key specification.
        fk_logical_name: The proposed name for the foreign key property.
        model_schema: The schema for the model on which the foreign key is proposed to
            be added.
        schemas: Used to resolve any $ref at the property level.

    Returns:
        Whether defining the foreign key is necessary given the model schema.

    """
    properties = model_schema["properties"]
    model_fk_spec = properties.get(fk_logical_name)
    if model_fk_spec is None:
        return True
    model_fk_spec = helpers.prepare_schema(schema=model_fk_spec, schemas=schemas)

    # Check type
    model_fk_type = model_fk_spec.get("type")
    if model_fk_type is None:
        raise exceptions.MalformedRelationshipError(
            f"{fk_logical_name} does not have a type. "
        )
    fk_type = fk_spec["type"]
    if model_fk_type != fk_type:
        raise exceptions.MalformedRelationshipError(
            "The foreign key required for the relationship has a different type than "
            "the property already defined under that name. "
            f"The required type is {fk_type}. "
            f"The {fk_logical_name} property has the {model_fk_type} type."
        )

    # Check foreign key constraint
    model_foreign_key = helpers.get_ext_prop(source=model_fk_spec, name="x-foreign-key")
    foreign_key = fk_spec["x-foreign-key"]
    if model_foreign_key is None:
        raise exceptions.MalformedRelationshipError(
            f"The property already defined under {fk_logical_name} does not define a "
            'foreign key constraint. Use the "x-foreign-key" extension property to '
            f'define a foreign key constraint, for example: "{foreign_key}".'
        )
    if model_foreign_key != foreign_key:
        raise exceptions.MalformedRelationshipError(
            "The foreign key required for the relationship has a different foreign "
            "key constraint than the property already defined under that name. "
            f"The required constraint is {foreign_key}. "
            f"The {fk_logical_name} property has the {model_foreign_key} constraint."
        )

    return False
