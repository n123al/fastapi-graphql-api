"""
Validation utilities for common data validation tasks.

This module provides validation functions for email addresses, usernames,
passwords, and other common data types used throughout the application.
"""

import re
import string
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise

    Example:
        ```python
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
        ```
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_pattern, email) is not None


def validate_username(username: str, min_length: int = 3, max_length: int = 50) -> bool:
    """
    Validate username format and requirements.

    Args:
        username: Username to validate
        min_length: Minimum username length (default: 3)
        max_length: Maximum username length (default: 50)

    Returns:
        True if username is valid, False otherwise

    Example:
        ```python
        >>> validate_username("john_doe")
        True
        >>> validate_username("ab")  # Too short
        False
        >>> validate_username("invalid@user")  # Contains invalid characters
        False
        ```
    """
    if not username or not isinstance(username, str):
        return False

    # Check length
    if len(username) < min_length or len(username) > max_length:
        return False

    # Allowed characters: alphanumeric, underscore, hyphen
    username_pattern = r"^[a-zA-Z0-9_-]+$"
    return re.match(username_pattern, username) is not None


def validate_password(
    password: str, requirements: Optional[dict] = None
) -> tuple[bool, list[str]]:
    """
    Validate password strength and requirements.

    Args:
        password: Password to validate
        requirements: Dictionary of password requirements
            - min_length: Minimum password length (default: 8)
            - require_uppercase: Require uppercase letters (default: True)
            - require_lowercase: Require lowercase letters (default: True)
            - require_numbers: Require numbers (default: True)
            - require_special: Require special characters (default: True)

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        ```python
        >>> validate_password("MyP@ssw0rd")
        (True, [])
        >>> validate_password("weak")
        (False, ['Password must be at least 8 characters long'])
        ```
    """
    if not password or not isinstance(password, str):
        return False, ["Password is required"]

    # Default requirements
    default_requirements: dict[str, Any] = {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
    }

    # Merge with provided requirements
    final_requirements = default_requirements.copy()
    if requirements:
        final_requirements.update(requirements)

    errors = []

    # Check minimum length
    if len(password) < final_requirements["min_length"]:
        errors.append(
            f"Password must be at least {final_requirements['min_length']} characters long"
        )

    # Check uppercase letters
    if final_requirements.get("require_uppercase") and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    # Check lowercase letters
    if final_requirements.get("require_lowercase") and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    # Check numbers
    if final_requirements.get("require_numbers") and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")

    # Check special characters
    if final_requirements.get("require_special") and not re.search(
        r'[!@#$%^&*(),.?":{}|<>]', password
    ):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def validate_object_id(object_id: str) -> bool:
    """
    Validate MongoDB ObjectId format.

    Args:
        object_id: ObjectId string to validate

    Returns:
        True if ObjectId format is valid, False otherwise

    Example:
        ```python
        >>> validate_object_id("507f1f77bcf86cd799439011")
        True
        >>> validate_object_id("invalid-id")
        False
        ```
    """
    if not object_id or not isinstance(object_id, str):
        return False

    try:
        ObjectId(object_id)
        return True
    except InvalidId:
        return False


def validate_phone_number(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate
        country_code: Country code for validation rules (default: US)

    Returns:
        True if phone format is valid, False otherwise

    Example:
        ```python
        >>> validate_phone_number("+1234567890")
        True
        >>> validate_phone_number("123-456-7890")
        True
        >>> validate_phone_number("invalid")
        False
        ```
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove common formatting characters
    cleaned_phone = re.sub(r"[\s\-\(\)\.]", "", phone)

    # Basic international phone pattern
    if cleaned_phone.startswith("+"):
        # International format: + followed by 1-15 digits
        return re.match(r"^\+\d{1,15}$", cleaned_phone) is not None
    else:
        # Assume US format if no country code specified
        # Accept 10 digits or 11 digits starting with 1
        us_pattern = r"^1?\d{10}$"
        return re.match(us_pattern, cleaned_phone) is not None


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file extension against allowed extensions.

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (with or without dot)

    Returns:
        True if extension is allowed, False otherwise

    Example:
        ```python
        >>> validate_file_extension("document.pdf", [".pdf", ".doc"])
        True
        >>> validate_file_extension("image.jpg", [".pdf", ".doc"])
        False
        ```
    """
    if not filename or not allowed_extensions:
        return False

    # Normalize extensions to include dot
    normalized_extensions = [
        ext if ext.startswith(".") else f".{ext}" for ext in allowed_extensions
    ]

    # Extract file extension
    file_ext = filename.lower().split(".")[-1] if "." in filename else ""
    file_ext_with_dot = f".{file_ext}" if file_ext else ""

    return file_ext_with_dot in normalized_extensions
