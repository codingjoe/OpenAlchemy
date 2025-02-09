"""Base class providing utilities for SQLAlchemy models."""

import datetime
import functools
import json
import typing

import jsonschema

from . import exceptions
from . import facades
from . import helpers
from . import types

TUtilityBase = typing.TypeVar("TUtilityBase", bound="UtilityBase")
TOptUtilityBase = typing.Optional[TUtilityBase]


class UtilityBase:
    """Base class providing utilities for SQLAlchemy models."""

    # Record of the schema used to construct the model. Myst be an object type. For all
    # columns any $ref must be resolved an allOf must be merged for all. Objects must
    # be recorded as a free-form object and have a x-de-$ref extension property with
    # the de-referenced name of the schema.
    _schema: types.Schema

    def __init__(self, **kwargs: typing.Any) -> None:
        """Construct."""
        raise NotImplementedError

    @classmethod
    def _get_schema(cls) -> types.Schema:
        """
        Get the schema.

        Raise ModelAttributeError if _schema is not defined.

        Returns:
            The schema.

        """
        # Checking for _schema
        if not hasattr(cls, "_schema"):
            raise exceptions.ModelAttributeError(
                "Model does not have a record of its schema. "
                "To support to_dict set the _schema class variable."
            )
        return cls._schema

    @classmethod
    def _get_properties(cls) -> types.Schema:
        """
        Get the properties from the schema.

        Raise ModelAttributeError if _schema is not defined.
        Raise MalformedSchemaError if the schema does not have any properties.

        Returns:
            The properties of the schema.

        """
        schema = cls._get_schema()
        # Checking that _schema has properties
        properties = schema.get("properties")
        if properties is None:
            raise exceptions.MalformedSchemaError(
                "The model schema does not have any properties."
            )
        return properties

    @staticmethod
    def _get_model(
        *, spec: types.Schema, name: str, schema: types.Schema
    ) -> typing.Type[TUtilityBase]:
        """Get the model based on the schema."""
        ref_model_name = helpers.get_ext_prop(source=spec, name="x-de-$ref")
        if ref_model_name is None:
            raise exceptions.MalformedSchemaError(
                "To construct object parameters the schema for the property must "
                "include the x-de-$ref extension property with the name of the "
                "model to construct for the property. "
                f"The property is {name}. "
                f"The model schema is {json.dumps(schema)}."
            )
        # Try to get model
        ref_model: TOptUtilityBase = facades.models.get_model(name=ref_model_name)
        if ref_model is None:
            raise exceptions.SchemaNotFoundError(
                f"The {ref_model_name} model was not found on open_alchemy.models."
            )
        return ref_model

    @staticmethod
    def _from_dict(
        kwargs: typing.Dict[str, typing.Any], *, model: typing.Type[TUtilityBase]
    ) -> TUtilityBase:
        """Construct model from dictionary."""
        return model.from_dict(**kwargs)

    @classmethod
    def from_dict(cls: typing.Type[TUtilityBase], **kwargs: typing.Any) -> TUtilityBase:
        """
        Construct model instance from a dictionary.

        Raise MalformedModelDictionaryError when the dictionary does not satisfy the
        model schema.

        Args:
            kwargs: The values to construct the class with.

        Returns:
            An instance of the model constructed using the dictionary.

        """
        # Check dictionary
        schema = cls._get_schema()
        try:
            jsonschema.validate(instance=kwargs, schema=schema)
        except jsonschema.ValidationError:
            raise exceptions.MalformedModelDictionaryError(
                "The dictionary passed to from_dict is not a valid instance of the "
                "model schema. "
                f"The expected schema is {json.dumps(schema)}. "
                f"The given value is {json.dumps(kwargs)}."
            )

        # Assemble dictionary for construction
        properties = cls._get_properties()
        model_dict: typing.Dict[str, typing.Any] = {}
        for name, value in kwargs.items():
            # Get the specification and type of the property
            spec = properties.get(name)
            if spec is None:
                raise exceptions.MalformedModelDictionaryError(
                    "A parameter was passed in that is not a property in the model "
                    "schema. "
                    f"The parameter is {name}. "
                    f"The model schema is {json.dumps(schema)}."
                )

            # Check readOnly
            read_only = spec.get("readOnly")
            if read_only is True:
                raise exceptions.MalformedModelDictionaryError(
                    "A parameter was passed in that is marked as readOnly in the "
                    "schema. "
                    f"The parameter is {name}. "
                    f"The model schema is {json.dumps(schema)}."
                )

            # Check type
            type_ = spec.get("type")
            format_ = spec.get("format")
            if type_ is None:
                raise exceptions.TypeMissingError(
                    f"The schema for the {name} property does not have a type."
                )

            # Handle object
            ref_model: typing.Type[TUtilityBase]
            if type_ == "object":
                ref_model = cls._get_model(spec=spec, name=name, schema=schema)
                ref_model_instance = cls._from_dict(value, model=ref_model)
                model_dict[name] = ref_model_instance
                continue

            if type_ == "array":
                item_spec = spec.get("items")
                if item_spec is None:
                    raise exceptions.MalformedSchemaError(
                        "To construct array parameters the schema for the property "
                        "must include the items property with the information about "
                        "the array items. "
                        f"The property is {name}. "
                        f"The model schema is {json.dumps(schema)}."
                    )
                ref_model = cls._get_model(spec=item_spec, name=name, schema=schema)
                model_from_dict = functools.partial(cls._from_dict, model=ref_model)
                ref_model_instances = map(model_from_dict, value)
                model_dict[name] = list(ref_model_instances)
                continue

            # Handle other types
            if format_ == "date-time":
                model_dict[name] = datetime.datetime.fromisoformat(value)
                continue
            model_dict[name] = value

        return cls(**model_dict)

    @staticmethod
    def _object_to_dict_relationship(
        *, value: typing.Any, name: str
    ) -> typing.Dict[str, typing.Any]:
        """Call to_dict on relationshup object."""
        try:
            return value.to_dict()
        except AttributeError:
            raise exceptions.InvalidModelInstanceError(
                f"The {name} object property instance does not have a to_dict "
                "implementation."
            )
        except TypeError:
            raise exceptions.InvalidModelInstanceError(
                f"The {name} object property instance to_dict implementation is "
                "expecting arguments."
            )

    @staticmethod
    def _object_to_dict_read_only(
        *, value: typing.Any, spec: types.Schema, name: str
    ) -> typing.Dict[str, typing.Any]:
        """Convert relationship to dictionary based on spec."""
        properties = spec.get("properties")
        if properties is None:
            raise exceptions.MalformedSchemaError(
                f"readOnly object definition {name} must have properties."
            )
        if not properties:
            raise exceptions.MalformedSchemaError(
                f"readOnly object definitions {name} must have at least 1 property."
            )
        return_dict = {}
        for key in properties.keys():
            return_dict[key] = getattr(value, key, None)
        return return_dict

    @classmethod
    def _object_to_dict(
        cls, value, name: str, spec: types.Schema, read_only: bool
    ) -> typing.Dict[str, typing.Any]:
        """Call to_dict on object."""
        if not read_only:
            return cls._object_to_dict_relationship(value=value, name=name)
        return cls._object_to_dict_read_only(value=value, name=name, spec=spec)

    @classmethod
    def _to_dict_property(
        cls,
        value: typing.Any,
        *,
        spec: types.Schema,
        name: str,
        array_context: bool = False,
        read_only: bool = False,
    ) -> typing.Any:
        """
        Perform property level to dict operation.

        Args:
            value: The value of the property.
            spec: The specification for the property.
            name: The name of the property.
            array_context: Whether array items are being worked on.
            read_only: Whether a readOnly property is being worked on.

        Returns:
            property value.

        """
        if not read_only:
            read_only = spec.get("readOnly", read_only)
        type_ = spec.get("type")
        format_ = spec.get("format")

        if type_ is None:
            schema_descriptor = "array item" if array_context else "property"
            raise exceptions.TypeMissingError(
                f"The {schema_descriptor} schema for the {name} property does not have "
                f"a type. The {schema_descriptor} schema is {json.dumps(spec)}."
            )

        # Handle array
        if type_ == "array":
            if array_context:
                raise exceptions.MalformedSchemaError(
                    "The array item schema cannot have the array type."
                )
            if value is None:
                return []
            item_spec = spec.get("items")
            if item_spec is None:
                raise exceptions.MalformedSchemaError(
                    "The array item schema must have an items property."
                )
            to_dict_property = functools.partial(
                cls._to_dict_property,
                spec=item_spec,
                name=name,
                array_context=True,
                read_only=read_only,
            )
            array_dict_values = map(to_dict_property, value)
            return list(array_dict_values)

        if value is None:
            return None

        # Handle object
        if type_ == "object":
            return cls._object_to_dict(
                value=value, name=name, spec=spec, read_only=read_only
            )

        # Handle other types
        if format_ == "date-time":
            return value.isoformat()
        return value

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        """
        Convert model instance to dictionary.

        Raise TypeMissingError if a property does not have a type.
        Raise InvalidModelInstanceError is an object to_dict call failed.

        Returns:
            The dictionary representation of the model.

        """
        properties = self._get_properties()

        # Collecting the values of the properties
        return_dict: typing.Dict[str, typing.Any] = {}
        for name, spec in properties.items():
            value = getattr(self, name, None)
            return_dict[name] = self._to_dict_property(
                spec=spec, name=name, value=value
            )

        return return_dict
