"""
GraphQL type definitions for the FastAPI GraphQL API.

This module contains all Strawberry GraphQL type definitions used throughout
the application, providing a centralized location for type management.
"""

from datetime import datetime
from typing import List, Optional

import strawberry


@strawberry.type
class Permission:
    """
    GraphQL Permission type representing access permissions.

    This type defines the structure of permission data, including
    resource and action specifications for fine-grained access control.
    """

    id: strawberry.ID
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class Role:
    """
    GraphQL Role type representing role-based access control.

    This type defines the structure of role data, including role metadata
    and status information for access control systems.
    """

    id: strawberry.ID
    name: str
    description: Optional[str] = None
    is_system_role: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @strawberry.field
    async def permissions(self, info: strawberry.types.Info) -> List[Permission]:
        """Get permissions assigned to this role."""
        from app.data.repositories import RoleRepository, PermissionRepository
        
        # self.id is strawberry.ID, convert to str
        role_id = str(self.id)
        role_repo = RoleRepository()
        role = await role_repo.get_by_id(role_id)
        
        if not role:
            return []
            
        perm_repo = PermissionRepository()
        permissions = []
        for perm_id in role.permission_ids:
            perm = await perm_repo.get_by_id(perm_id)
            if perm:
                permissions.append(
                    Permission(
                        id=strawberry.ID(str(perm.id)),
                        name=perm.name,
                        description=perm.description,
                        resource=perm.resource,
                        action=perm.action,
                        is_active=perm.is_active,
                        created_at=perm.created_at,
                        updated_at=perm.updated_at,
                    )
                )
        return permissions


@strawberry.type
class User:
    """
    GraphQL User type representing user information.

    This type defines the structure of user data exposed through GraphQL,
    including basic profile information, status fields, and timestamps.
    """

    id: strawberry.ID
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @strawberry.field
    async def roles(self, info: strawberry.types.Info) -> List[Role]:
        """Get roles assigned to this user."""
        from app.data.repositories import UserRepository, RoleRepository
        
        user_id = str(self.id)
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            return []
            
        role_repo = RoleRepository()
        roles = []
        for role_id in user.role_ids:
            role = await role_repo.get_by_id(role_id)
            if role:
                roles.append(
                    Role(
                        id=strawberry.ID(str(role.id)),
                        name=role.name,
                        description=role.description,
                        is_system_role=role.is_system_role,
                        is_active=role.is_active,
                        created_at=role.created_at,
                        updated_at=role.updated_at,
                    )
                )
        return roles

    @strawberry.field
    async def permissions(self, info: strawberry.types.Info) -> List[str]:
        """
        Get all permission names available to this user.
        Includes direct permissions and permissions inherited from roles.
        """
        from app.core.auth_strategies import AuthorizationService
        
        user_id = str(self.id)
        auth_service = AuthorizationService()
        return await auth_service.get_user_permissions(user_id)


@strawberry.type
class Group:
    """
    GraphQL Group type representing user groups.

    This type defines the structure of group data for organizing
    users and managing collective permissions.
    """

    id: strawberry.ID
    name: str
    description: Optional[str] = None
    is_system_group: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Input types for mutations
@strawberry.input
class UserInput:
    """
    Input type for user creation and updates.

    This type defines the required and optional fields for creating
    or updating user records through GraphQL mutations.
    """

    username: str
    email: str
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


@strawberry.input
class RoleInput:
    """
    Input type for role creation and updates.

    This type defines the required and optional fields for managing
    role data through GraphQL mutations.
    """

    name: str
    description: Optional[str] = None
    is_system_role: Optional[bool] = False
    is_active: Optional[bool] = True


@strawberry.input
class PermissionInput:
    """
    Input type for permission creation and updates.

    This type defines the required and optional fields for managing
    permission data through GraphQL mutations.
    """

    name: str
    description: Optional[str] = None
    resource: str
    action: str
    is_active: Optional[bool] = True


@strawberry.input
class GroupInput:
    """
    Input type for group creation and updates.

    This type defines the required and optional fields for managing
    group data through GraphQL mutations.
    """

    name: str
    description: Optional[str] = None
    is_system_group: Optional[bool] = False
    is_active: Optional[bool] = True


@strawberry.input
class LoginInput:
    identifier: str
    password: str


@strawberry.input
class SetPasswordInput:
    token: str
    password: str


@strawberry.type
class AuthPayload:
    accessToken: str
    refreshToken: str
    tokenType: str
    expiresIn: int


@strawberry.type
class AccessTokenPayload:
    accessToken: str
    tokenType: str
    expiresIn: int
