"""
Group data model for managing user groups and organizations.

This module defines the Group model which represents collections of users
with shared permissions and access rights within the system.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import ConfigDict, EmailStr, Field, field_validator

from .base import BaseDataModel


class Group(BaseDataModel):
    """
    Group data model representing user collections with shared permissions.

    Groups are used to organize users and manage access control at scale.
    They can represent departments, teams, projects, or any logical grouping
    that requires shared permissions and resources.

    Attributes:
        name: Unique name identifier for the group
        description: Detailed description of the group's purpose
        group_type: Classification of the group (department, team, project, etc.)
        owner_id: User ID of the group owner/creator
        member_ids: List of user IDs who are members of this group
        permission_ids: List of permission IDs granted to this group
        settings: Group-specific configuration settings
        metadata: Additional flexible data storage
        max_members: Maximum allowed members (None for unlimited)
        is_public: Whether the group is publicly discoverable
        requires_approval: Whether membership requires approval

    Example:
        ```python
        group = Group(
            name="engineering-team",
            description="Engineering department members",
            group_type="department",
            owner_id="user123",
            member_ids=["user123", "user456"],
            permission_ids=["perm1", "perm2"],
            is_public=False,
            requires_approval=True
        )
        ```
    """

    # Core group attributes
    name: str = Field(
        ..., min_length=1, max_length=100, description="Unique group name"
    )
    description: str = Field(
        default="", max_length=500, description="Group description"
    )
    group_type: str = Field(
        default="general", description="Type of group (department, team, project)"
    )

    # Ownership and membership
    owner_id: str = Field(..., description="ID of the group owner/creator")
    member_ids: List[str] = Field(
        default_factory=list, description="List of member user IDs"
    )
    permission_ids: List[str] = Field(
        default_factory=list, description="List of permission IDs"
    )

    # Group settings and configuration
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Group configuration settings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Access control
    max_members: Optional[int] = Field(
        default=None, description="Maximum number of members"
    )
    is_public: bool = Field(
        default=False, description="Whether group is publicly discoverable"
    )
    requires_approval: bool = Field(
        default=True, description="Whether membership requires approval"
    )

    # Timestamps for group lifecycle
    created_at: Optional[datetime] = Field(
        default=None, description="Group creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="Soft deletion timestamp"
    )

    # Status flags
    is_active: bool = Field(default=True, description="Whether the group is active")
    is_deleted: bool = Field(default=False, description="Whether the group is deleted")
    version: int = Field(default=1, description="Record version for optimistic locking")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate group name format."""
        if not v.strip():
            raise ValueError("Group name cannot be empty")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Group name must be alphanumeric with hyphens and underscores only"
            )
        return v.lower().strip()

    @field_validator("group_type")
    @classmethod
    def validate_group_type(cls, v: str) -> str:
        """Validate group type."""
        valid_types = {
            "general",
            "department",
            "team",
            "project",
            "organization",
            "system",
        }
        if v not in valid_types:
            raise ValueError(f"Group type must be one of: {valid_types}")
        return v

    @field_validator("max_members")
    @classmethod
    def validate_max_members(cls, v: Optional[int]) -> Optional[int]:
        """Validate maximum members constraint."""
        if v is not None and v < 1:
            raise ValueError("Maximum members must be at least 1")
        return v

    def add_member(self, user_id: str) -> bool:
        """
        Add a user to the group.

        Args:
            user_id: ID of the user to add

        Returns:
            True if user was added, False if already a member

        Raises:
            ValueError: If max_members limit would be exceeded
        """
        if user_id in self.member_ids:
            return False

        if self.max_members and len(self.member_ids) >= self.max_members:
            raise ValueError(
                f"Group has reached maximum capacity of {self.max_members} members"
            )

        self.member_ids.append(user_id)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def remove_member(self, user_id: str) -> bool:
        """
        Remove a user from the group.

        Args:
            user_id: ID of the user to remove

        Returns:
            True if user was removed, False if not a member
        """
        if user_id not in self.member_ids:
            return False

        self.member_ids.remove(user_id)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def add_permission(self, permission_id: str) -> bool:
        """
        Add a permission to the group.

        Args:
            permission_id: ID of the permission to add

        Returns:
            True if permission was added, False if already assigned
        """
        if permission_id in self.permission_ids:
            return False

        self.permission_ids.append(permission_id)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def remove_permission(self, permission_id: str) -> bool:
        """
        Remove a permission from the group.

        Args:
            permission_id: ID of the permission to remove

        Returns:
            True if permission was removed, False if not assigned
        """
        if permission_id not in self.permission_ids:
            return False

        self.permission_ids.remove(permission_id)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def is_member(self, user_id: str) -> bool:
        """
        Check if a user is a member of this group.

        Args:
            user_id: ID of the user to check

        Returns:
            True if user is a member, False otherwise
        """
        return user_id in self.member_ids

    def is_owner(self, user_id: str) -> bool:
        """
        Check if a user is the owner of this group.

        Args:
            user_id: ID of the user to check

        Returns:
            True if user is the owner, False otherwise
        """
        return self.owner_id == user_id

    def get_member_count(self) -> int:
        """
        Get the current number of members in the group.

        Returns:
            Number of group members
        """
        return len(self.member_ids)

    def can_add_member(self) -> bool:
        """
        Check if more members can be added to the group.

        Returns:
            True if members can be added, False if at capacity
        """
        if self.max_members is None:
            return True
        return len(self.member_ids) < self.max_members

    def soft_delete(self) -> None:
        """
        Soft delete the group by marking it as deleted.

        This method sets the deleted_at timestamp and is_deleted flag
        without actually removing the record from storage.
        """
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """
        Restore a soft-deleted group.

        This method clears the deleted_at timestamp and is_deleted flag,
        making the group active again.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(
        self, exclude_none: bool = True, exclude_sensitive: bool = True
    ) -> Dict[str, Any]:
        """
        Convert the group to a dictionary representation.

        Returns:
            Dictionary containing all group attributes
        """
        data = (
            self.model_dump(exclude_none=exclude_none)
            if hasattr(self, "model_dump")
            else self.dict(exclude_none=exclude_none)
        )
        if exclude_sensitive:
            data.pop("settings", None)
            data.pop("metadata", None)
        return data

    def to_response_dict(self) -> Dict[str, Any]:
        """
        Convert the group to a response-friendly dictionary.

        Returns:
            Dictionary with sensitive fields excluded for API responses
        """
        data = self.to_dict(exclude_none=True, exclude_sensitive=True)
        # Remove internal fields that shouldn't be exposed in API responses
        data.pop("settings", None)
        data.pop("metadata", None)
        return data

    model_config = ConfigDict(
        populate_by_name=True, use_enum_values=True, validate_assignment=True
    )
