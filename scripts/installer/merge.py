from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = deepcopy(dict(base))
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, Mapping):
            result[key] = deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = deepcopy(result[key]) + deepcopy(value)
        else:
            result[key] = deepcopy(value)
    return result


def merge_hook_configs(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return deepcopy(incoming)
    return deep_merge(existing, incoming)
