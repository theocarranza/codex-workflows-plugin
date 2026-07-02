from typing import Any


def evaluate_output(output: Any, manifest: dict[str, Any]) -> list[str]:
    """Validate task output against the skill manifest output_signature."""
    critiques: list[str] = []
    expected_signature = manifest.get("output_signature", {})
    if not expected_signature:
        return critiques

    expected_type = expected_signature.get("type", "object")
    if expected_type == "object" and not isinstance(output, dict):
        critiques.append(f"Expected output to be a dictionary/object, but got {type(output).__name__}.")
        return critiques

    if expected_type != "object":
        return critiques

    expected_properties = expected_signature.get("properties", {})
    for key in expected_signature.get("required", []):
        if key not in output:
            critiques.append(f"Missing required output property '{key}'.")

    for prop_name, prop_schema in expected_properties.items():
        if prop_name not in output:
            continue
        actual_value = output[prop_name]
        expected_prop_type = prop_schema.get("type")
        if expected_prop_type == "string" and not isinstance(actual_value, str):
            critiques.append(f"Property '{prop_name}' should be a string, got {type(actual_value).__name__}.")
        elif expected_prop_type == "boolean" and not isinstance(actual_value, bool):
            critiques.append(f"Property '{prop_name}' should be a boolean, got {type(actual_value).__name__}.")
        elif expected_prop_type == "number" and not isinstance(actual_value, (int, float)):
            critiques.append(f"Property '{prop_name}' should be a number, got {type(actual_value).__name__}.")

    return critiques
