"""
Role data models and schemas.

This module defines the Pydantic models for role-related data, providing
validation and serialization for role information throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.data.models.base import BaseDataModel


class Role(BaseDataModel):
    """
    Role data model for role-based access control.
    
    This class represents a role in the system, defining permissions
    and access levels that can be assigned to users.
    """
    
    # Basic role information
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    description: Optional[str] = Field(default=None, max_length=500, description="Role description")
    
    # Role type and status
    is_system_role: bool = Field(default=False, description="Whether this is a system role that cannot be deleted")
    
    # Permissions (stored as IDs)
    permission_ids: List[str] = Field(default_factory=list, description="Permission IDs assigned to this role")
    
    # Users assigned to this role (stored as IDs)
    user_ids: List[str] = Field(default_factory=list, description="User IDs assigned to this role")
    
    def has_permission(self, permission_id: str) -> bool:
        """
        Check if role has specific permission.
        
        Args:
            permission_id: ID of the permission to check
            
        Returns:
            True if role has the permission, False otherwise
        """
        return permission_id in self.permission_ids
    
    def add_permission(self, permission_id: str) -> None:
        """
        Add permission to role.
        
        Args:
            permission_id: ID of the permission to add
        """
        if permission_id not in self.permission_ids:
            self.permission_ids.append(permission_id)
            self.update_timestamp()
    
    def remove_permission(self, permission_id: str) -> None:
        """
        Remove permission from role.
        
        Args:
            permission_id: ID of the permission to remove
        """
        if permission_id in self.permission_ids:
            self.permission_ids.remove(permission_id)
            self.update_timestamp()
    
    def get_permission_ids(self) -> List[str]:
        """
        Get list of permission IDs.
        
        Returns:
            Copy of the permission IDs list
        """
        return self.permission_ids.copy()
    
    def add_user(self, user_id: str) -> None:
        """
        Add user to role.
        
        Args:
            user_id: ID of the user to add
        """
        if user_id not in self.user_ids:
            self.user_ids.append(user_id)
            self.update_timestamp()
    
    def remove_user(self, user_id: str) -> None:
        """
        Remove user from role.
        
        Args:
            user_id: ID of the user to remove
        """
        if user_id in self.user_ids:
            self.user_ids.remove(user_id)
            self.update_timestamp()
    
    def get_user_ids(self) -> List[str]:
        """
        Get list of user IDs assigned to this role.
        
        Returns:
            Copy of the user IDs list
        """
        return self.user_ids.copy()
    
    def can_be_deleted(self) -> bool:
        """
        Check if role can be deleted.
        
        Returns:
            True if role can be deleted, False if it's a system role
        """
        return not self.is_system_role
    
    def to_response_dict(self) -> Dict[str, Any]:
        """
        Convert role to response dictionary.
        
        Returns:
            Dictionary with safe role data for API responses
        """
        return {
            "id": getattr(self, 'id', None),
            "name": self.name,
            "description": self.description,
            "is_system_role": self.is_system_role,
            "is_active": self.is_active,
            "permission_ids": self.permission_ids,
            "user_ids": self.user_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role(name='{self.name}', is_system_role={self.is_system_role})>"
    
    def __str__(self) -> str:
        """String representation of the role."""
        return self.name