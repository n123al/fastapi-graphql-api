"""
GraphQL mutation resolvers for User entities.

This module contains all GraphQL mutation operations related to user management,
including user creation, updates, deletions, and user state management.
"""

import strawberry
from strawberry.types import Info
from typing import Optional, Any
from datetime import datetime

from app.services.user import UserService
from app.data.repositories import UserRepository
from app.graphql.types.types import User, UserInput
from app.graphql.auth import require_permission, require_any_permission, get_current_user, require_authentication
from app.core.utils.helpers import generate_random_string
from app.core.utils.validators import validate_password
from app.core.utils.helpers import send_email_smtp
from app.core.security import create_set_password_token
from app.core import settings


class UserMutations:
    """
    GraphQL mutation resolvers for user-related operations.
    
    This class contains all mutation methods for modifying user data,
    including creation, updates, deletion, and user-specific operations.
    """
    
    @staticmethod
    def _to_graphql_user(user_data: Any) -> User:
        if hasattr(user_data, 'model_dump'):
            data_dict = user_data.model_dump()
        elif hasattr(user_data, 'dict'):
            data_dict = user_data.dict()
        else:
            data_dict = user_data
        full_name = None
        if 'profile' in data_dict and isinstance(data_dict['profile'], dict):
            full_name = data_dict['profile'].get('full_name')
        return User(
            id=strawberry.ID(str(data_dict.get('id'))),
            username=data_dict.get('username'),
            email=data_dict.get('email'),
            full_name=full_name,
            is_active=data_dict.get('is_active', True),
            is_superuser=data_dict.get('is_superuser', False),
            created_at=data_dict.get('created_at'),
            updated_at=data_dict.get('updated_at')
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
            Exception: If service validation fails or user creation fails
            
        Note:
            Automatically adds timestamps and sets initial user state
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
                        raise Exception("Failed to generate a valid password")
            user_data = {
                "username": input.username,
                "email": input.email,
                "password": password_value,
                "full_name": input.full_name
            }
            
            # Create user through service
            created_user = await user_service.create_user(user_data)
            if settings.ONBOARDING_EMAIL_ENABLED:
                token = create_set_password_token({
                    "sub": str(created_user.id),
                    "email": created_user.email
                })
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
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def update_user(self, info: Info, id: strawberry.ID, input: UserInput) -> Optional[User]:
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
            
        Note:
            Only updates provided fields and automatically updates the timestamp
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                from app.core.exceptions import AuthenticationError
                raise AuthenticationError("Authentication required")
            
            # Check if user is updating their own profile or has permission to update others
            user_id = str(id)
            if current_user.id != user_id and not await info.context.has_permission("users:update"):
                from app.core.exceptions import AuthorizationError
                raise AuthorizationError(
                    "Permission 'users:update' required to update other users' profiles",
                    code="INSUFFICIENT_PERMISSIONS"
                )
            
            user_service = UserService(UserRepository())
            
            # Prepare update data for service layer
            update_data = {
                "username": input.username,
                "email": input.email,
                "full_name": input.full_name
            }
            
            # Update user through service
            updated_user = await user_service.update_user(user_id, update_data)
            
            if updated_user:
                return self._to_graphql_user(updated_user)
            
            return None
        except Exception as e:
            # Re-raise authentication/authorization errors
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise
            raise Exception(f"Failed to update user: {str(e)}")
    
    @require_permission("users:delete")
    async def delete_user(self, info: Info, id: strawberry.ID) -> bool:
        """
        Soft delete a user by marking them as inactive.
        Requires users:delete permission.
        
        Args:
            info: GraphQL context info
            id: The unique identifier of the user to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            AuthorizationError: If user lacks permission to delete users
            
        Note:
            Performs soft delete (sets is_active: false) rather than permanent deletion
        """
        try:
            user_service = UserService(UserRepository())
            deleted = await user_service.deactivate_user(str(id))
            return deleted is not None
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
            
        Note:
            Similar to delete_user but more explicit about the operation intent
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                from app.core.exceptions import AuthenticationError
                raise AuthenticationError("Authentication required")
            
            # Check if user is deactivating their own account or has permission to deactivate others
            user_id = str(id)
            if current_user.id != user_id and not await info.context.has_permission("users:deactivate"):
                from app.core.exceptions import AuthorizationError
                raise AuthorizationError(
                    "Permission 'users:deactivate' required to deactivate other users' accounts",
                    code="INSUFFICIENT_PERMISSIONS"
                )
            
            user_service = UserService(UserRepository())
            deactivated_user = await user_service.deactivate_user(user_id)
            
            if deactivated_user:
                return self._to_graphql_user(deactivated_user)
            
            return None
        except Exception as e:
            # Re-raise authentication/authorization errors
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise
            raise Exception(f"Failed to deactivate user: {str(e)}")

    @require_permission("users:create")
    async def send_onboarding_email(self, info: Info, id: strawberry.ID) -> bool:
        try:
            if not settings.ONBOARDING_EMAIL_ENABLED:
                return False
            user_service = UserService(UserRepository())
            user = await user_service.get_by_id(str(id))
            if not user:
                return False
            token = create_set_password_token({
                "sub": str(user.id),
                "email": user.email
            })
            subject = "Set your password"
            base = settings.SET_PASSWORD_URL_BASE
            if base:
                param = settings.SET_PASSWORD_URL_PARAM
                sep = "&" if "?" in base else "?"
                link = f"{base}{sep}{param}={token}"
                body = f"Click to set your password: {link}"
            else:
                body = f"Use this token to set your password: {token}"
            return send_email_smtp(user.email, subject, body)
        except Exception:
            return False