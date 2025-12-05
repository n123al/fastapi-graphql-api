"""
GraphQL query resolvers for User entities.

This module contains all GraphQL query operations related to user management,
including fetching individual users, user lists, and user-specific data.
"""

from typing import Any, List, Optional

import strawberry
from strawberry.types import Info

from app.data.repositories import UserRepository
from app.graphql.auth import (
    get_current_user,
    require_authentication,
    require_permission,
)
from app.graphql.types.types import User
from app.services.user import UserService


class UserQueries:
    """
    GraphQL query resolvers for user-related operations.

    This class contains all query methods for retrieving user data,
    including individual users, user lists, and user-specific information.
    """

    @staticmethod
    def _to_graphql_user(user_data: Any) -> User:
        """
        Convert database User model to GraphQL User type.

        Args:
            user_data: User data from database (Pydantic model or dict)

        Returns:
            GraphQL User type with only the expected fields
        """
        full_name = ""
        if hasattr(user_data, "get_full_name"):
            full_name = user_data.get_full_name()

        if hasattr(user_data, "model_dump"):
            data_dict = user_data.model_dump()
        elif hasattr(user_data, "dict"):
            data_dict = user_data.dict()
        else:
            data_dict = user_data

        # If full_name wasn't retrieved from method, try to get from profile
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

    async def user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """
        Retrieve a single user by their unique identifier.
        Users can access their own data with basic authentication.
        Accessing other users requires users:read permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the user to retrieve

        Returns:
            User object if found and authorized, None otherwise

        Raises:
            AuthorizationError if user lacks permission to access this data
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)

            user_service = UserService(UserRepository())
            target_user_data = await user_service.get_by_id(str(id))

            if not target_user_data:
                return None

            # If accessing own data, allow with basic authentication
            if current_user and str(target_user_data.id) == str(current_user.id):
                return self._to_graphql_user(target_user_data)

            # If accessing other user's data, require specific permission
            if not await info.context.has_permission("users:read"):
                from app.core.exceptions import AuthorizationError

                raise AuthorizationError(
                    "Permission 'users:read' required to access other users' data",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            return self._to_graphql_user(target_user_data)

        except Exception as e:
            # Re-raise authentication/authorization errors
            from app.core.exceptions import AuthorizationError

            if isinstance(e, AuthorizationError):
                raise
            print(f"Error in user query: {str(e)}")
            return None

    @require_permission("users:read")
    async def users(self, info: Info, limit: int = 100) -> List[User]:
        """
        List all registered accounts.
        Requires users:read permission.

        Args:
            info: GraphQL context info
            limit: Maximum number of users to return (default: 100)

        Returns:
            List of User objects, empty list if no users found or service errors

        Raises:
            AuthorizationError if user lacks users:read permission

        Note:
            Returns both active and inactive users, but excludes deleted users.
        """
        try:
            user_service = UserService(UserRepository())
            users_data = await user_service.get_users(limit=limit)

            users = []
            for user_data in users_data:
                users.append(self._to_graphql_user(user_data))

            return users
        except Exception as e:
            # Log the error instead of silently swallowing it
            print(f"Error in users query: {str(e)}")
            import traceback

            traceback.print_exc()
            return []

    async def user_by_username(self, info: Info, username: str) -> Optional[User]:
        """
        Retrieve a user by their username.
        Users can access their own data with basic authentication.
        Accessing other users requires users:read permission.

        Args:
            info: GraphQL context info
            username: The username to search for

        Returns:
            User object if found and authorized, None otherwise

        Raises:
            AuthorizationError if user lacks permission to access this data
        """
        try:
            # Get current user from context
            current_user = await info.context.get_current_user()

            user_service = UserService(UserRepository())
            target_user_data = await user_service.get_by_username(username)

            if not target_user_data:
                return None

            # If accessing own data, allow with basic authentication
            if current_user and target_user_data.username == current_user.username:
                return self._to_graphql_user(target_user_data)

            # If accessing other user's data, require specific permission
            if not await info.context.has_permission("users:read"):
                from app.core.exceptions import AuthorizationError

                raise AuthorizationError(
                    "Permission 'users:read' required to access other users' data",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            return self._to_graphql_user(target_user_data)

        except Exception as e:
            # Re-raise authentication/authorization errors
            from app.core.exceptions import AuthorizationError

            if isinstance(e, AuthorizationError):
                raise
            print(f"Error in user_by_username query: {str(e)}")
            return None

    @require_authentication()
    async def me(self, info: Info) -> Optional[User]:
        """
        Retrieve the currently authenticated user.
        Requires authentication.

        Args:
            info: GraphQL context info

        Returns:
            User object for the current user

        Raises:
            AuthenticationError if user is not authenticated
        """
        try:
            # Get current user from context - require_authentication ensures this is not None
            current_user = await get_current_user(info)

            if not current_user:
                # This should ideally be caught by the decorator, but as a safeguard
                from app.core.exceptions import AuthenticationError

                raise AuthenticationError("Authentication required")

            return self._to_graphql_user(current_user)

        except Exception as e:
            # Re-raise authentication errors
            from app.core.exceptions import AuthenticationError

            if isinstance(e, AuthenticationError):
                raise
            print(f"Error in me query: {str(e)}")
            return None

    async def user_by_email(self, info: Info, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        Users can access their own data with basic authentication.
        Accessing other users requires users:read permission.

        Args:
            info: GraphQL context info
            email: The email address to search for

        Returns:
            User object if found and authorized, None otherwise

        Raises:
            AuthorizationError if user lacks permission to access this data
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)

            user_service = UserService(UserRepository())
            target_user_data = await user_service.get_by_email(email)

            if not target_user_data:
                return None

            # If accessing own data, allow with basic authentication
            if current_user and target_user_data.email == current_user.email:
                return self._to_graphql_user(target_user_data)

            # If accessing other user's data, require specific permission
            if not await info.context.has_permission("users:read"):
                from app.core.exceptions import AuthorizationError

                raise AuthorizationError(
                    "Permission 'users:read' required to access other users' data",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            return self._to_graphql_user(target_user_data)

        except Exception as e:
            # Re-raise authentication/authorization errors
            from app.core.exceptions import AuthorizationError

            if isinstance(e, AuthorizationError):
                raise
            print(f"Error in user_by_email query: {str(e)}")
            return None
