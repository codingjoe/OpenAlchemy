"""Generate columns based on openapi schema property."""

import re
import typing

import sqlalchemy

from openapi_sqlalchemy import exceptions
from openapi_sqlalchemy import helpers
from openapi_sqlalchemy import types

_REF_PATTER = re.compile(r"^#\/components\/schemas\/(\w+)$")


@helpers.testing_guard(environment_name="TESTING")
def resolve_ref(func: typing.Callable) -> typing.Callable:
    """Resolve $ref schemas."""

    def inner(
        *, spec: types.SchemaSpec, schemas: types.Schemas, logical_name: str, **kwargs
    ) -> sqlalchemy.Column:
        """Replace function."""
        schema = types.Schema(logical_name=logical_name, spec=spec)
        ref_schema = helpers.resolve_ref(schema=schema, schemas=schemas)
        return func(logical_name=logical_name, spec=ref_schema.spec, **kwargs)

    return inner


@resolve_ref
@helpers.add_logical_name
def column_factory(
    *, spec: types.SchemaSpec, required: typing.Optional[bool] = None
) -> sqlalchemy.Column:
    """
    Generate column based on openapi schema property.

    Args:
        spec: The schema for the column.
        required: Whether the object property is required.

    Returns:
        The SQLAlchemy column based on the schema.

    """
    if "type" not in spec:
        raise exceptions.TypeMissingError("Every property requires a type.")

    # Keep track of column arguments
    type_: typing.Optional[sqlalchemy.sql.type_api.TypeEngine] = None
    args: typing.Tuple[typing.Any, ...] = ()
    kwargs: typing.Dict[str, typing.Any] = {}

    # Calculate column modifiers
    kwargs["nullable"] = _calculate_nullable(spec=spec, required=required)
    if spec.get("x-primary-key"):
        kwargs["primary_key"] = True
    if spec.get("x-index"):
        kwargs["index"] = True
    if spec.get("x-unique"):
        kwargs["unique"] = True

    # Calculating type of column
    if spec.get("type") == "integer":
        type_ = _handle_integer(spec=spec)
    elif spec.get("type") == "number":
        type_ = _handle_number(spec=spec)
    elif spec.get("type") == "string":
        type_ = _handle_string(spec=spec)
    elif spec.get("type") == "boolean":
        type_ = sqlalchemy.Boolean

    if type_ is None:
        raise exceptions.FeatureNotImplementedError(
            f"{spec['type']} has not been implemented"
        )

    return sqlalchemy.Column(type_, *args, **kwargs)


def _handle_object(*, spec: types.SchemaSpec) -> types.SchemaSpec:
    """
    Determine the foreign key schema for an object reference.

    Args:
        spec: The schema of the object reference.

    Returns:
        The foreign key schema.

    """
    tablename = spec.get("x-tablename")
    if not tablename:
        raise exceptions.MalformedObjectSchemaError(
            "Referenced object is missing x-tablename property."
        )
    properties = spec.get("properties")
    if properties is None:
        raise exceptions.MalformedObjectSchemaError(
            "Referenced object does not have any properties."
        )
    id_spec = properties.get("id")
    if id_spec is None:
        raise exceptions.MalformedObjectSchemaError(
            "Referenced object does not have id property."
        )
    id_type = id_spec.get("type")
    if id_type is None:
        raise exceptions.MalformedObjectSchemaError(
            "Referenced object id property does not have a type."
        )

    return {"type": id_type, "x-foreign-key": f"{tablename}.id"}


def _calculate_nullable(
    *, spec: types.SchemaSpec, required: typing.Optional[bool]
) -> bool:
    """
    Calculate the value of the nullable field.

    The following is the truth table for the nullable property.
    required  | schema nullable | returned nullable
    --------------------------------------------------------
    None      | not given       | True
    None      | False           | False
    None      | True            | True
    False     | not given       | True
    False     | False           | False
    False     | True            | True
    True      | not given       | False
    True      | False           | False
    True      | True            | True

    To summarize, if nullable is the schema the value for it is used. Otherwise True
    is returned unless required is True.

    Args:
        spec: The schema for the column.
        required: Whether the property is required.

    Returns:
        The nullable value for the column.

    """
    nullable = spec.get("nullable")
    if nullable is None:
        if required:
            return False
        return True
    if nullable:
        return True
    return False


def _handle_integer(
    *, spec: types.SchemaSpec
) -> typing.Union[sqlalchemy.Integer, sqlalchemy.BigInteger]:
    """
    Determine the type of integer to use for the schema.

    Args:
        spec: The schema for the integer column.

    Returns:
        Integer or BigInteger depending on the format.

    """
    if spec.get("format", "int32") == "int32":
        return sqlalchemy.Integer
    if spec.get("format") == "int64":
        return sqlalchemy.BigInteger
    raise exceptions.FeatureNotImplementedError(
        f"{spec.get('format')} format for integer is not supported."
    )


def _handle_number(*, spec: types.SchemaSpec) -> sqlalchemy.Float:
    """
    Determine the type of number to use for the schema.

    Args:
        spec: The schema for the number column.

    Returns:
        Float.

    """
    if spec.get("format", "float") == "float":
        return sqlalchemy.Float
    raise exceptions.FeatureNotImplementedError(
        f"{spec.get('format')} format for number is not supported."
    )


def _handle_string(*, spec: types.SchemaSpec) -> sqlalchemy.String:
    """
    Determine the setup of the string to use for the schema.

    Args:
        spec: The schema for the string column.

    Returns:
        String.

    """
    return sqlalchemy.String(length=spec.get("maxLength"))
