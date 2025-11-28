"""
Data layer package containing all data models, schemas, and database configurations.

This package provides the data access layer for the application, including:
- Data models and Pydantic schemas
- Database connection configurations  
- Data transformation utilities
- Repository interfaces and implementations
"""

from app.data.models.base import BaseDataModel
from app.data.models.group import Group
from app.data.models.permission import Permission
from app.data.models.role import Role
from app.data.models.user import User, UserPreferences, UserProfile
from app.data.repositories import (
    BaseRepository,
    GroupRepository,
    PermissionRepository,
    RoleRepository,
    UserRepository,
)

__all__ = [
    'BaseDataModel',
    'User', 'UserProfile', 'UserPreferences',
    'Role', 'Permission', 'Group',
    'BaseRepository',
    'UserRepository',
    'RoleRepository',
    'PermissionRepository',
    'GroupRepository'
]