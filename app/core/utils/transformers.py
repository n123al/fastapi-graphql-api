"""
Data transformation utilities for converting between different data formats.

This module provides functions for transforming data between different formats
such as camelCase/snakeCase conversion, datetime serialization, and other
common data transformation tasks.
"""

import re
from datetime import datetime
from typing import Any, Callable, Dict, Union


def dict_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from snake_case to camelCase.

    Args:
        data: Dictionary with snake_case keys

    Returns:
        Dictionary with camelCase keys

    Example:
        ```python
        >>> data = {"user_name": "john", "created_at": "2023-01-01"}
        >>> dict_to_camel_case(data)
        {'userName': 'john', 'createdAt': '2023-01-01'}
        ```
    """

    def snake_to_camel(snake_str: str) -> str:
        """Convert snake_case string to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    return {snake_to_camel(key): value for key, value in data.items()}


def dict_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from camelCase to snake_case.

    Args:
        data: Dictionary with camelCase keys

    Returns:
        Dictionary with snake_case keys

    Example:
        ```python
        >>> data = {"userName": "john", "createdAt": "2023-01-01"}
        >>> dict_to_snake_case(data)
        {'user_name': 'john', 'created_at': '2023-01-01'}
        ```
    """

    def camel_to_snake(camel_str: str) -> str:
        """Convert camelCase string to snake_case."""
        # Insert underscore before capital letters (except the first character)
        snake_str = re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str)
        return snake_str.lower()

    return {camel_to_snake(key): value for key, value in data.items()}


def serialize_datetime(
    dt: Union[datetime, None], format_string: str = "%Y-%m-%dT%H:%M:%S.%fZ"
) -> Union[str, None]:
    """
    Serialize datetime object to ISO format string.

    Args:
        dt: Datetime object to serialize
        format_string: Format string for datetime (default: ISO format)

    Returns:
        Serialized datetime string or None

    Example:
        ```python
        >>> from datetime import datetime
        >>> dt = datetime(2023, 1, 1, 12, 0, 0)
        >>> serialize_datetime(dt)
        '2023-01-01T12:00:00.000000Z'
        ```
    """
    if dt is None:
        return None

    return dt.strftime(format_string)


def deserialize_datetime(
    dt_str: Union[str, None], format_string: str = "%Y-%m-%dT%H:%M:%S.%fZ"
) -> Union[datetime, None]:
    """
    Deserialize datetime string to datetime object.

    Args:
        dt_str: Datetime string to deserialize
        format_string: Format string for datetime parsing

    Returns:
        Datetime object or None

    Example:
        ```python
        >>> deserialize_datetime("2023-01-01T12:00:00.000000Z")
        datetime.datetime(2023, 1, 1, 12, 0)
        ```
    """
    if dt_str is None:
        return None

    try:
        return datetime.strptime(dt_str, format_string)
    except ValueError:
        # Try common alternative formats
        alternative_formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f%z",
        ]

        for alt_format in alternative_formats:
            try:
                return datetime.strptime(dt_str, alt_format)
            except ValueError:
                continue

        # If all formats fail, return None
        return None


def transform_keys_recursive(data: Any, transform_func: Callable[[str], str]) -> Any:
    """
    Recursively transform dictionary keys using the provided function.

    Args:
        data: Data structure to transform (dict, list, or primitive)
        transform_func: Function to transform keys

    Returns:
        Transformed data structure

    Example:
        ```python
        >>> data = {"user_info": {"first_name": "John", "last_name": "Doe"}}
        >>> transform_keys_recursive(data, snake_to_camel)
        {'userInfo': {'firstName': 'John', 'lastName': 'Doe'}}
        ```
    """
    if isinstance(data, dict):
        return {
            transform_func(key): transform_keys_recursive(value, transform_func)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [transform_keys_recursive(item, transform_func) for item in data]
    else:
        return data


def flatten_dict(
    nested_dict: Dict[str, Any], separator: str = ".", prefix: str = ""
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary into a single-level dictionary.

    Args:
        nested_dict: Dictionary to flatten
        separator: Separator for nested keys (default: '.')
        prefix: Prefix for keys (used in recursion)

    Returns:
        Flattened dictionary

    Example:
        ```python
        >>> data = {"user": {"profile": {"name": "John"}}, "age": 25}
        >>> flatten_dict(data)
        {'user.profile.name': 'John', 'age': 25}
        ```
    """
    flattened = {}

    for key, value in nested_dict.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            flattened.update(flatten_dict(value, separator, new_key))
        else:
            flattened[new_key] = value

    return flattened


def unflatten_dict(flat_dict: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Unflatten a flattened dictionary back to nested structure.

    Args:
        flat_dict: Flattened dictionary
        separator: Separator used in keys (default: '.')

    Returns:
        Nested dictionary

    Example:
        ```python
        >>> data = {'user.profile.name': 'John', 'user.profile.age': 25}
        >>> unflatten_dict(data)
        {'user': {'profile': {'name': 'John', 'age': 25}}}
        ```
    """
    result: Dict[str, Any] = {}

    for key, value in flat_dict.items():
        keys = key.split(separator)
        current = result

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    return result
