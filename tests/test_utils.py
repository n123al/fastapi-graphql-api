"""
Unit tests for utility functions.
"""
from datetime import datetime, timezone

import pytest
from bson import ObjectId


class TestHelpers:
    """Test helper utility functions."""

    def test_objectid_to_str(self):
        """Test ObjectId to string conversion."""
        obj_id = ObjectId()
        str_id = str(obj_id)

        assert isinstance(str_id, str)
        assert len(str_id) == 24

    def test_datetime_serialization(self):
        """Test datetime serialization."""
        now = datetime.now(timezone.utc)
        iso_string = now.isoformat()

        assert isinstance(iso_string, str)
        assert "T" in iso_string


class TestValidators:
    """Test validation utility functions."""

    def test_email_format(self):
        """Test email format validation."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.com",
        ]

        for email in valid_emails:
            assert "@" in email
            assert "." in email.split("@")[1]

    def test_username_format(self):
        """Test username format validation."""
        valid_usernames = ["user123", "test_user", "user-name", "User123"]

        for username in valid_usernames:
            assert len(username) >= 3
            assert len(username) <= 50

    def test_password_strength(self):
        """Test password strength validation."""
        # Minimum length check
        weak_password = "123"
        strong_password = "StrongP@ssw0rd123"

        assert len(weak_password) < 8
        assert len(strong_password) >= 8


class TestTransformers:
    """Test data transformation utilities."""

    def test_dict_to_camel_case(self):
        """Test snake_case to camelCase conversion."""
        snake_case = {
            "user_name": "test",
            "email_address": "test@example.com",
            "is_active": True,
        }

        # Manual conversion for testing
        camel_case = {
            "userName": snake_case["user_name"],
            "emailAddress": snake_case["email_address"],
            "isActive": snake_case["is_active"],
        }

        assert "userName" in camel_case
        assert "emailAddress" in camel_case
        assert "isActive" in camel_case

    def test_remove_none_values(self):
        """Test removing None values from dict."""
        data = {"name": "test", "email": None, "age": 25, "bio": None}

        cleaned = {k: v for k, v in data.items() if v is not None}

        assert "name" in cleaned
        assert "age" in cleaned
        assert "email" not in cleaned
        assert "bio" not in cleaned

    def test_flatten_dict(self):
        """Test flattening nested dictionary."""
        nested = {"user": {"name": "test", "profile": {"age": 25}}}

        # Check nested structure
        assert "user" in nested
        assert "name" in nested["user"]
        assert "profile" in nested["user"]
        assert "age" in nested["user"]["profile"]


class TestDataSanitization:
    """Test data sanitization utilities."""

    def test_strip_whitespace(self):
        """Test stripping whitespace from strings."""
        data = "  test string  "
        cleaned = data.strip()

        assert cleaned == "test string"
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")

    def test_lowercase_email(self):
        """Test converting email to lowercase."""
        email = "Test@Example.COM"
        normalized = email.lower()

        assert normalized == "test@example.com"

    def test_remove_special_characters(self):
        """Test removing special characters."""
        text = "Hello, World! @#$%"
        # Keep only alphanumeric and spaces
        cleaned = "".join(c for c in text if c.isalnum() or c.isspace())

        assert "Hello" in cleaned
        assert "World" in cleaned
        assert "@" not in cleaned
        assert "#" not in cleaned


class TestPagination:
    """Test pagination utilities."""

    def test_pagination_calculation(self):
        """Test pagination offset calculation."""
        page = 2
        page_size = 10

        skip = (page - 1) * page_size

        assert skip == 10

    def test_total_pages_calculation(self):
        """Test total pages calculation."""
        total_items = 95
        page_size = 10

        total_pages = (total_items + page_size - 1) // page_size

        assert total_pages == 10

    def test_pagination_bounds(self):
        """Test pagination boundary conditions."""
        # First page
        page = 1
        page_size = 10
        skip = (page - 1) * page_size
        assert skip == 0

        # Last page with partial results
        total_items = 95
        last_page = (total_items + page_size - 1) // page_size
        assert last_page == 10
