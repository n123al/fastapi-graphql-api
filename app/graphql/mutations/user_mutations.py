"""
GraphQL mutation resolvers for User entities.

This module contains all GraphQL mutation operations related to user management,
including user creation, updates, deletions, and user state management.
"""

from datetime import datetime
from typing import Any, Optional

import strawberry
from strawberry.types import Info

from app.core import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ValidationError,
)
from app.core.security import create_set_password_token
from app.core.utils.helpers import generate_random_string, send_email_smtp
from app.core.utils.validators import validate_password
from app.data.repositories import UserRepository
from app.graphql.auth import (
    check_permission,
    get_current_user,
    require_any_permission,
    require_authentication,
    require_permission,
)
from app.graphql.types.types import User, UserInput
from app.services.user import UserService


class UserMutations:
    """
    GraphQL mutation resolvers for user-related operations.

    This class contains all mutation methods for modifying user data,
    including creation, updates, deletion, and user-specific operations.
    """

    @staticmethod
    def _to_graphql_user(user_data: Any) -> User:
        full_name = ""
        if hasattr(user_data, "get_full_name"):
            full_name = user_data.get_full_name()

        if hasattr(user_data, "model_dump"):
            data_dict = user_data.model_dump()
        elif hasattr(user_data, "dict"):
            data_dict = user_data.dict()
        else:
            data_dict = user_data

        if (
            not full_name
            and "profile" in data_dict
            and isinstance(data_dict["profile"], dict)
        ):
            full_name = data_dict["profile"].get("full_name") or ""

        return User(
            id=strawberry.ID(str(data_dict.get("id"))),
            username=data_dict.get("username"),
            email=data_dict.get("email"),
            full_name=full_name,
            is_active=data_dict.get("is_active", True),
            is_superuser=data_dict.get("is_superuser", False),
            created_at=data_dict.get("created_at"),
            updated_at=data_dict.get("updated_at"),
        )

    @require_permission("users:create")
    async def create_user(self, info: Info, input: UserInput) -> User:
        """
        Create a new user with the provided input data.
        Requires users:create permission.

        Args:
            info: GraphQL context info
            input: UserInput object containing user creation data

        Returns:
            The newly created User object

        Raises:
            AuthorizationError: If user lacks permission to create users
            ConflictError: If username or email already exists
            ValidationError: If input data is invalid
            Exception: If user creation fails
        """
        try:
            user_service = UserService(UserRepository())

            # Prepare user data for service layer
            password_value = input.password
            if not password_value:
                attempts = 0
                while attempts < 5:
                    candidate = generate_random_string(16)
                    is_valid, _ = validate_password(candidate)
                    if is_valid:
                        password_value = candidate
                        break
                    attempts += 1
                if not password_value:
                    candidate = generate_random_string(24)
                    is_valid, _ = validate_password(candidate)
                    if is_valid:
                        password_value = candidate
                    else:
                        raise ValidationError("Failed to generate a valid password")
            user_data = {
                "username": input.username,
                "email": input.email,
                "password": password_value,
                "full_name": input.full_name,
            }

            # Create user through service
            created_user = await user_service.create_user(user_data)
            if settings.ONBOARDING_EMAIL_ENABLED:
                token = create_set_password_token(
                    {"sub": str(created_user.id), "email": created_user.email}
                )
                subject = "Set your password"
                base = settings.SET_PASSWORD_URL_BASE
                if base:
                    param = settings.SET_PASSWORD_URL_PARAM
                    sep = "&" if "?" in base else "?"
                    link = f"{base}{sep}{param}={token}"
                    body = f"Click to set your password: {link}"
                else:
                    body = f"Use this token to set your password: {token}"
                send_email_smtp(created_user.email, subject, body)
            return self._to_graphql_user(created_user)
        except (
            ConflictError,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
        ):
            raise
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")

    async def update_user(
        self, info: Info, id: strawberry.ID, input: UserInput
    ) -> Optional[User]:
        """
        Update an existing user with the provided input data.
        Users can update their own profile without special permissions.
        Updating other users requires users:update permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the user to update
            input: UserInput object containing updated user data

        Returns:
            Updated User object if successful, None otherwise

        Raises:
            AuthorizationError: If user lacks permission to update this user
            ConflictError: If username or email already exists
            ValidationError: If input data is invalid
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                raise AuthenticationError("Authentication required")

            # Check if user is updating their own profile or has permission to update others
            user_id = str(id)
            if current_user.id != user_id and not await check_permission(
                info, "users:update"
            ):
                raise AuthorizationError(
                    "Permission 'users:update' required to update other users' profiles",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            user_service = UserService(UserRepository())

            # Prepare update data for service layer
            update_data = {
                "username": input.username,
                "email": input.email,
                "full_name": input.full_name,
            }

            # Update user through service
            updated_user = await user_service.update_user(user_id, update_data)

            if updated_user:
                return self._to_graphql_user(updated_user)

            return None
        except (
            ConflictError,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
        ):
            raise
        except Exception as e:
            raise Exception(f"Failed to update user: {str(e)}")

    @require_permission("users:delete")
    async def delete_user(self, info: Info, id: strawberry.ID) -> bool:
        """
        Delete a user.
        Requires users:delete permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the user to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            AuthorizationError: If user lacks permission to delete users
        """
        try:
            user_service = UserService(UserRepository())
            deleted = await user_service.delete(str(id))
            return deleted
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            raise Exception(f"Failed to delete user: {str(e)}")

    @require_permission("users:activate")
    async def activate_user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """
        Activate a previously deactivated user.
        Requires users:activate permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the user to activate

        Returns:
            Updated User object if successful, None otherwise

        Raises:
            AuthorizationError: If user lacks permission to activate users
        """
        try:
            user_service = UserService(UserRepository())
            activated_user = await user_service.activate_user(str(id))

            if activated_user:
                return self._to_graphql_user(activated_user)

            return None
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            raise Exception(f"Failed to activate user: {str(e)}")

    async def deactivate_user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """
        Deactivate a user without permanently deleting them.
        Users can deactivate their own account without special permissions.
        Deactivating other users requires users:deactivate permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the user to deactivate

        Returns:
            Updated User object if successful, None otherwise

        Raises:
            AuthorizationError: If user lacks permission to deactivate this user
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                raise AuthenticationError("Authentication required")

            # Check if user is deactivating their own account or has permission to deactivate others
            user_id = str(id)
            if current_user.id != user_id and not await check_permission(
                info, "users:deactivate"
            ):
                raise AuthorizationError(
                    "Permission 'users:deactivate' required to deactivate other users' accounts",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            user_service = UserService(UserRepository())
            deactivated_user = await user_service.deactivate_user(user_id)

            if deactivated_user:
                return self._to_graphql_user(deactivated_user)

            return None
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            raise Exception(f"Failed to deactivate user: {str(e)}")
