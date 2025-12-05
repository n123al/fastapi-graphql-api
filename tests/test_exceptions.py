"""
Unit tests for custom exceptions.
"""
import pytest

from app.core.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)


class TestApplicationError:
    """Test ApplicationError exception."""

    def test_application_error_creation(self):
        """Test creating an ApplicationError."""
        error = ApplicationError("Test error", "TEST_ERROR")

        assert error.message == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.details == {}

    def test_application_error_with_details(self):
        """Test ApplicationError with details."""
        details = {"field": "username", "issue": "already exists"}
        error = ApplicationError("Test error", "TEST_ERROR", details)

        assert error.details == details

    def test_application_error_string_representation(self):
        """Test string representation of ApplicationError."""
        error = ApplicationError("Test error", "TEST_ERROR")
        error_str = str(error)

        assert "Test error" in error_str


class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_authentication_error_creation(self):
        """Test creating an AuthenticationError."""
        error = AuthenticationError("Invalid credentials")

        assert error.message == "Invalid credentials"
        assert error.code == "AUTH_FAILED"

    def test_authentication_error_custom_code(self):
        """Test AuthenticationError with custom code."""
        error = AuthenticationError("Token expired", "TOKEN_EXPIRED")

        assert error.message == "Token expired"
        assert error.code == "TOKEN_EXPIRED"


class TestAuthorizationError:
    """Test AuthorizationError exception."""

    def test_authorization_error_creation(self):
        """Test creating an AuthorizationError."""
        error = AuthorizationError("Access denied")

        assert error.message == "Access denied"
        assert error.code == "ACCESS_DENIED"

    def test_authorization_error_custom_code(self):
        """Test AuthorizationError with custom code."""
        error = AuthorizationError(
            "Insufficient permissions", "INSUFFICIENT_PERMISSIONS"
        )

        assert error.message == "Insufficient permissions"
        assert error.code == "INSUFFICIENT_PERMISSIONS"


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        error = ValidationError("Invalid input")

        assert error.message == "Invalid input"
        assert error.code == "VALIDATION_ERROR"

    def test_validation_error_with_details(self):
        """Test ValidationError with field details."""
        details = {"email": "Invalid email format"}
        error = ValidationError("Validation failed")
        error.details = details

        assert error.details == details


class TestNotFoundError:
    """Test NotFoundError exception."""

    def test_not_found_error_creation(self):
        """Test creating a NotFoundError."""
        error = NotFoundError("User not found")

        assert error.message == "User not found"
        assert error.code == "NOT_FOUND"

    def test_not_found_error_with_resource(self):
        """Test NotFoundError with resource type."""
        error = NotFoundError("Resource not found", "RESOURCE_NOT_FOUND")

        assert error.code == "RESOURCE_NOT_FOUND"


class TestExceptionInheritance:
    """Test exception inheritance."""

    def test_authentication_error_is_application_error(self):
        """Test that AuthenticationError inherits from ApplicationError."""
        error = AuthenticationError("Test")

        assert isinstance(error, ApplicationError)

    def test_authorization_error_is_application_error(self):
        """Test that AuthorizationError inherits from ApplicationError."""
        error = AuthorizationError("Test")

        assert isinstance(error, ApplicationError)

    def test_validation_error_is_application_error(self):
        """Test that ValidationError inherits from ApplicationError."""
        error = ValidationError("Test")

        assert isinstance(error, ApplicationError)

    def test_not_found_error_is_application_error(self):
        """Test that NotFoundError inherits from ApplicationError."""
        error = NotFoundError("Test")

        assert isinstance(error, ApplicationError)
