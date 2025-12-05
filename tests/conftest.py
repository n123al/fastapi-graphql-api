import asyncio
import os
import sys
from typing import AsyncGenerator
from unittest.mock import Mock

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.motor_database import motor_db_manager
from app.data.models.group import Group
from app.data.models.permission import Permission
from app.data.models.role import Role
from app.data.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=False)
async def setup_test_database():
    """Set up test database before running tests."""
    # Use a separate test database
    test_db_name = f"{settings.DATABASE_NAME}_test"

    # Create test database client
    client = AsyncIOMotorClient(settings.MONGODB_URL)

    # Drop test database if it exists
    try:
        await client.drop_database(test_db_name)
    except Exception:
        pass  # Database might not exist

    # Initialize motor database manager with test database
    motor_db_manager.client = client
    motor_db_manager.database = client[test_db_name]
    motor_db_manager.is_connected = True

    yield motor_db_manager

    # Cleanup after tests
    try:
        await client.drop_database(test_db_name)
    except Exception:
        pass
    motor_db_manager.is_connected = False
    client.close()


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "hashed_password": "$2b$12$testhash",
    }


@pytest.fixture
def test_role_data():
    """Provide test role data."""
    return {"name": "test_role", "description": "Test role for testing"}


@pytest.fixture
def test_permission_data():
    """Provide test permission data."""
    return {"name": "test:permission", "description": "Test permission for testing"}


@pytest.fixture
def test_group_data():
    """Provide test group data."""
    return {"name": "test_group", "description": "Test group for testing"}


@pytest.fixture
def test_permission(test_permission_data) -> dict:
    """Create a test permission."""
    return test_permission_data


@pytest.fixture
def test_role(test_role_data, test_permission) -> dict:
    """Create a test role with permission."""
    role_data = test_role_data.copy()
    role_data["permissions"] = [test_permission["name"]]
    return role_data


@pytest.fixture
def test_group(test_group_data) -> dict:
    """Create a test group."""
    return test_group_data


@pytest.fixture
def test_user(test_user_data, test_role) -> dict:
    """Create a test user with role."""
    user_data = test_user_data.copy()
    user_data["role"] = test_role["name"]
    return user_data


@pytest.fixture
def mock_user():
    """Provide a mock user object."""
    user = Mock(spec=User)
    user.id = "test_user_id"
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.is_superuser = False
    user.has_permission = Mock(return_value=True)
    user.has_role = Mock(return_value=False)
    user.has_any_permission = Mock(return_value=True)
    user.is_member_of = Mock(return_value=False)
    return user


@pytest.fixture
def mock_role():
    """Provide a mock role object."""
    role = Mock(spec=Role)
    role.id = "test_role_id"
    role.name = "test_role"
    role.description = "Test role"
    role.permissions = []
    role.is_system_role = False
    role.is_active = True
    return role


@pytest.fixture
def mock_permission():
    """Provide a mock permission object."""
    permission = Mock(spec=Permission)
    permission.id = "test_permission_id"
    permission.name = "test:permission"
    permission.description = "Test permission"
    permission.resource = "test"
    permission.action = "permission"
    permission.full_permission = "test:permission"
    permission.is_active = True
    return permission


@pytest.fixture
def mock_group():
    """Provide a mock group object."""
    group = Mock(spec=Group)
    group.id = "test_group_id"
    group.name = "test_group"
    group.description = "Test group"
    group.is_system_group = False
    group.is_active = True
    return group
