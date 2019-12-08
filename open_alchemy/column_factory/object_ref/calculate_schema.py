"""Calculate the object schema from the artifacts."""

from open_alchemy import types


def calculate_schema(*, artifacts: types.ObjectArtifacts) -> types.ObjectSchema:
    """
    Calculate the object schema from the artifacts.

    Args:
        artifacts: The artifactsfor the object reference.

    Returns:
        The schema for the object to store with the model.

    """
    return {"type": "object", "x-de-$ref": artifacts.ref_model_name}
