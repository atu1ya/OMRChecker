"""Generic serialization utilities for dataclasses and other objects.

This module provides generic serialization functions that handle nested
structures, Path objects, Enums, and collections without circular dependencies.
"""

from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def dataclass_to_dict(obj: Any) -> dict | list | Any:
    """Recursively convert a dataclass instance to a dictionary.

    Handles nested dataclasses, Path objects, Enums, lists, dicts, and other types.
    This provides a generic serialization solution that automatically adapts to
    dataclass structure changes without requiring manual field mapping.

    Args:
        obj: The object to serialize (typically a dataclass instance)

    Returns:
        Dictionary representation suitable for JSON serialization

    Examples:
        >>> @dataclass
        >>> class Config:
        ...     path: Path
        ...     value: int = 10
        >>> config = Config(path=Path("/tmp/test"), value=42)
        >>> dataclass_to_dict(config)
        {'path': '/tmp/test', 'value': 42}

    Supported Types:
        - Primitive types: str, int, float, bool, None
        - Dataclasses: Automatically serialized recursively
        - Path objects: Converted to strings
        - Enums: Converted to their values
        - Collections: Lists, tuples, and dicts are handled recursively
        - Nested structures: Any combination of the above
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        # Convert dataclass to dict and recursively process fields
        return {key: dataclass_to_dict(value) for key, value in asdict(obj).items()}
    if isinstance(obj, Path):
        # Convert Path to string
        return str(obj)
    if isinstance(obj, Enum):
        # Convert Enum to its value
        return obj.value
    if isinstance(obj, dict):
        # Recursively process dictionary values
        return {key: dataclass_to_dict(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        # Recursively process list/tuple items
        return [dataclass_to_dict(item) for item in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        # Primitive types pass through as-is
        return obj
    # For other types, try to convert to string
    # This handles datetime, custom objects, etc.
    try:
        return str(obj)
    except Exception:
        # If all else fails, return the object as-is
        return obj
