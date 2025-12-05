"""
Unit tests for security module.
"""
from datetime import datetime, timedelta

import pytest

from app.core.exceptions import TokenError
from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hash_generation(self):
        """Test that password hashing generates a hash."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "test_password"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(TokenError):
            decode_token(invalid_token)

    def test_token_expiration(self):
        """Test token with expiration."""
        data = {"sub": "user123"}
        # Create token with default expiration
        token = create_access_token(data)

        # Should decode successfully immediately
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        # Token should have expiration
        assert "exp" in decoded

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert "exp" in decoded
        assert isinstance(decoded["exp"], (int, float))


class TestSecurityHelpers:
    """Test security helper functions."""

    def test_empty_password_hash(self):
        """Test hashing empty password."""
        password = ""
        hashed = get_password_hash(password)

        assert hashed is not None
        assert verify_password(password, hashed) is True

    def test_long_password_hash(self):
        """Test hashing very long password."""
        password = "a" * 1000
        hashed = get_password_hash(password)

        assert hashed is not None
        assert verify_password(password, hashed) is True

    def test_special_characters_password(self):
        """Test password with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "пароль密码🔐"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
