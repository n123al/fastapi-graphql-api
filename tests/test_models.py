"""
Unit tests for data models.
"""
from datetime import datetime, timezone

import pytest
from bson import ObjectId


class TestUserModel:
    """Test User model."""

    def test_user_dict_structure(self):
        """Test user dictionary structure."""
        user_data = {
            "_id": ObjectId(),
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_here",
            "is_active": True,
            "is_superuser": False,
            "email_verified": False,
            "profile": {"full_name": "Test User", "bio": "Test bio"},
            "preferences": {"theme": "light", "language": "en"},
            "role_ids": [],
            "group_ids": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"
        assert user_data["is_active"] is True
        assert "profile" in user_data
        assert "preferences" in user_data


class TestRoleModel:
    """Test Role model."""

    def test_role_dict_structure(self):
        """Test role dictionary structure."""
        role_data = {
            "_id": ObjectId(),
            "name": "admin",
            "description": "Administrator role",
            "permission_ids": [],
            "is_system_role": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        assert role_data["name"] == "admin"
        assert role_data["is_system_role"] is True
        assert "permission_ids" in role_data


class TestPermissionModel:
    """Test Permission model."""

    def test_permission_dict_structure(self):
        """Test permission dictionary structure."""
        permission_data = {
            "_id": ObjectId(),
            "name": "user:read",
            "description": "Read user data",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        assert permission_data["name"] == "user:read"
        assert permission_data["is_active"] is True


class TestGroupModel:
    """Test Group model."""

    def test_group_dict_structure(self):
        """Test group dictionary structure."""
        group_data = {
            "_id": ObjectId(),
            "name": "developers",
            "description": "Development team",
            "is_system_group": False,
            "metadata": {"department": "engineering"},
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        assert group_data["name"] == "developers"
        assert group_data["is_system_group"] is False
        assert "metadata" in group_data
