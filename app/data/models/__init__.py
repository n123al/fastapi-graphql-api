"""
Data models package containing all Pydantic models and schemas.

This module defines the data structures used throughout the application,
providing type safety and validation for all data operations.
"""

from app.data.models.base import BaseDataModel
from app.data.models.group import Group
from app.data.models.permission import Permission
from app.data.models.role import Role
from app.data.models.user import User, UserPreferences, UserProfile

__all__ = [
    "BaseDataModel",
    "User",
    "UserProfile",
    "UserPreferences",
    "Role",
    "Permission",
    "Group",
]
