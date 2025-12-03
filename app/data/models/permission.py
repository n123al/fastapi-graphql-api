"""
Permission data models and schemas.

This module defines the Pydantic models for permission-related data, providing
validation and serialization for permission information throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.data.models.base import BaseDataModel


class Permission(BaseDataModel):
    """
    Permission data model for role-based access control.

    This class represents a permission in the system, defining specific
    actions that can be performed on resources.
    """

    # Basic permission information
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Permission description"
    )

    # Resource and action specification
    resource: str = Field(
        ..., max_length=50, description="Resource this permission applies to"
    )
    action: str = Field(..., max_length=50, description="Action this permission grants")

    # System permission flag
    is_system_permission: bool = Field(
        default=False,
        description="Whether this is a system permission that cannot be deleted",
    )

    @property
    def full_permission(self) -> str:
        """
        Get full permission string in format 'resource:action'.

        Returns:
            Full permission string
        """
        return f"{self.resource}:{self.action}"

    @property
    def permission_key(self) -> str:
        """
        Get a unique key for this permission.

        Returns:
            Unique permission key based on resource and action
        """
        return f"{self.resource}:{self.action}"

    def matches_resource(self, resource: str) -> bool:
        """
        Check if permission matches a specific resource.

        Args:
            resource: Resource name to check

        Returns:
            True if permission matches the resource, False otherwise
        """
        return self.resource == resource

    def matches_action(self, action: str) -> bool:
        """
        Check if permission matches a specific action.

        Args:
            action: Action name to check

        Returns:
            True if permission matches the action, False otherwise
        """
        return self.action == action

    def can_perform(self, resource: str, action: str) -> bool:
        """
        Check if permission allows performing action on resource.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            True if permission allows the action on the resource, False otherwise
        """
        return self.resource == resource and self.action == action

    def can_be_deleted(self) -> bool:
        """
        Check if permission can be deleted.

        Returns:
            True if permission can be deleted, False if it's a system permission
        """
        return not self.is_system_permission

    def to_response_dict(self) -> Dict[str, Any]:
        """
        Convert permission to response dictionary.

        Returns:
            Dictionary with safe permission data for API responses
        """
        return {
            "id": getattr(self, "id", None),
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "full_permission": self.full_permission,
            "permission_key": self.permission_key,
            "is_system_permission": self.is_system_permission,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission(name='{self.name}', key='{self.resource}:{self.action}')>"

    def __str__(self) -> str:
        """String representation of the permission."""
        return self.full_permission
