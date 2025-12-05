from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.data.models.user import User
from app.services.user import UserService


class TestUserServiceExtended:
    @pytest.mark.asyncio
    async def test_create_user_persists_full_name(self):
        repo_mock = Mock()
        repo_mock.create = AsyncMock()
        repo_mock.get_by_username = AsyncMock(return_value=None)
        repo_mock.get_by_email = AsyncMock(return_value=None)

        service = UserService(repo_mock)

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
            "full_name": "Test User",
        }

        # Mock return value of create
        created_user_mock = MagicMock(spec=User)
        created_user_mock.id = "123"
        created_user_mock.username = "testuser"
        created_user_mock.email = "test@example.com"
        repo_mock.create.return_value = created_user_mock

        await service.create_user(user_data)

        # Verify create was called with correct data
        # The argument to create is a User object
        call_args = repo_mock.create.call_args[0][0]
        # We check if the profile dict inside the User object has full_name
        # Since we can't easily inspect the Pydantic model instance constructed inside create_user
        # without full mocking, we rely on checking if the attribute is set.
        assert call_args.profile.full_name == "Test User"

    @pytest.mark.asyncio
    async def test_get_users_includes_inactive(self):
        repo_mock = Mock()
        repo_mock.get_all = AsyncMock()

        service = UserService(repo_mock)

        await service.get_users(limit=10, skip=5)

        repo_mock.get_all.assert_called_with(
            limit=10, skip=5, is_active={"$in": [True, False]}
        )

    @pytest.mark.asyncio
    async def test_update_user_full_name(self):
        repo_mock = Mock()
        repo_mock.update = AsyncMock()
        repo_mock.get_by_id = AsyncMock()  # Correct method name

        # Mock existing user
        existing_user = MagicMock(spec=User)
        existing_user.username = "olduser"
        existing_user.email = "old@example.com"
        existing_user.profile = MagicMock()
        existing_user.profile.dict.return_value = {"full_name": "Old Name"}
        repo_mock.get_by_id.return_value = existing_user

        service = UserService(repo_mock)

        await service.update_user("123", {"full_name": "New Name"})

        # Verify update was called
        call_args = repo_mock.update.call_args
        assert call_args[0][0] == "123"
        update_dict = call_args[0][1]
        assert update_dict["profile"]["full_name"] == "New Name"
