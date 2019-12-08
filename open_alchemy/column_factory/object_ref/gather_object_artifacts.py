"""Gather artifacts for constructing an object reference."""

# from open_alchemy import types


# def gather_object_artifacts(
#     *, schema: types.Schema, logical_name: str, schemas: types.Schemas
# ) -> types.ObjectArtifacts:
#     """
#     Gather artifacts for constructing an object reference.

#     The schema must contain any of $ref and allOf. In the case of allOf, the array
# must
#     contain exactly one $ref.

#     Raises MalformedSchemaError if the schema does not include a $ref nor allOf with a
#         $ref.

#     Args:
#         schema: The schema of the object reference.
#         logical_name: The property name of the object reference.
#         schemas: Used to resolve any $ref.

#     Returns:
#         The object artifacts required for construction.

#     """
#     return types.ObjectArtifacts(None, None, None)
