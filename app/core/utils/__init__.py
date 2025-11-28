"""
Core utilities package containing shared utility functions and helpers.

This package provides common utility functions that are used across the application,
including validation helpers, data transformation utilities, and common operations.
"""

from .helpers import (
    format_file_size,
    generate_random_string,
    sanitize_html,
    truncate_text,
)
from .transformers import (
    deserialize_datetime,
    dict_to_camel_case,
    dict_to_snake_case,
    serialize_datetime,
)
from .validators import (
    validate_email,
    validate_object_id,
    validate_password,
    validate_username,
)

__all__ = [
    # Validators
    "validate_email",
    "validate_username",
    "validate_password",
    "validate_object_id",
    # Transformers
    "dict_to_camel_case",
    "dict_to_snake_case",
    "serialize_datetime",
    "deserialize_datetime",
    # Helpers
    "generate_random_string",
    "sanitize_html",
    "truncate_text",
    "format_file_size",
]
