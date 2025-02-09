"""Generate columns based on OpenAPI schema property."""

import re
import typing

import sqlalchemy

from open_alchemy import exceptions
from open_alchemy import helpers
from open_alchemy import types

from . import array_ref
from . import column
from . import object_ref
from . import read_only

_REF_PATTER = re.compile(r"^#\/components\/schemas\/(\w+)$")


def column_factory(
    *,
    spec: types.Schema,
    schemas: types.Schemas,
    required: typing.Optional[bool] = None,
    logical_name: str,
    model_schema: types.Schema,
) -> typing.Tuple[typing.List[typing.Tuple[str, sqlalchemy.Column]], types.Schema]:
    """
    Generate column based on OpenAPI schema property.

    Args:
        spec: The schema for the column.
        schemas: Used to resolve any $ref.
        required: Whether the object property is required.
        logical_name: The logical name in the specification for the schema.
        model_schema: The schema for the model.

    Returns:
        The logical name, the SQLAlchemy column based on the schema and the
        specification to store for the column.

    """
    # Check readOnly
    if helpers.peek.read_only(schema=spec, schemas=schemas):
        return read_only.handle_read_only(schema=spec, schemas=schemas)

    # Check type
    type_ = helpers.peek.type_(schema=spec, schemas=schemas)

    if type_ == "object":
        # Handle objects
        return object_ref.handle_object(
            spec=spec,
            schemas=schemas,
            required=required,
            logical_name=logical_name,
            model_schema=model_schema,
        )

    if type_ == "array":
        # Handle arrays
        return array_ref.handle_array(
            spec=spec,
            model_schema=model_schema,
            schemas=schemas,
            logical_name=logical_name,
        )

    # Handle columns
    spec, spec_column = column.handle_column(
        schema=spec, schemas=schemas, required=required
    )
    return ([(logical_name, spec_column)], spec)
