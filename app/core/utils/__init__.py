"""
Core utilities package containing shared utility functions and helpers.

This package provides common utility functions that are used across the application,
including validation helpers, data transformation utilities, and common operations.
"""

from .validators import (
    validate_email,
    validate_username,
    validate_password,
    validate_object_id
)

from .transformers import (
    dict_to_camel_case,
    dict_to_snake_case,
    serialize_datetime,
    deserialize_datetime
)

from .helpers import (
    generate_random_string,
    sanitize_html,
    truncate_text,
    format_file_size
)

__all__ = [
    # Validators
    'validate_email',
    'validate_username',
    'validate_password',
    'validate_object_id',
    
    # Transformers
    'dict_to_camel_case',
    'dict_to_snake_case',
    'serialize_datetime',
    'deserialize_datetime',
    
    # Helpers
    'generate_random_string',
    'sanitize_html',
    'truncate_text',
    'format_file_size'
]