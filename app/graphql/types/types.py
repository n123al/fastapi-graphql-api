"""
GraphQL type definitions for the FastAPI GraphQL API.

This module contains all Strawberry GraphQL type definitions used throughout
the application, providing a centralized location for type management.
"""

import strawberry
from typing import Optional
from datetime import datetime


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