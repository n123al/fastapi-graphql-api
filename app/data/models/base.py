"""
Base data model providing common functionality for all data models.

This module defines the base class that all data models inherit from,
providing common fields, methods, and utilities for data operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseDataModel(BaseModel):
    """
    Base data model providing common fields and functionality.

    This class serves as the foundation for all data models in the application,
    providing common fields like timestamps and utility methods for data transformation.
    """

    id: Optional[str] = Field(default=None, description="Record identifier")
    # Common timestamp fields
    created_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the record was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the record was last updated"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the record was soft deleted"
    )

    # Status fields
    is_active: bool = Field(default=True, description="Whether the record is active")
    is_deleted: bool = Field(
        default=False, description="Whether the record is soft deleted"
    )

    # Metadata
    version: int = Field(default=1, description="Record version for optimistic locking")

    model_config = ConfigDict(
        validate_assignment=True, use_enum_values=True, arbitrary_types_allowed=True
    )

    def to_dict(
        self, exclude_none: bool = True, exclude_sensitive: bool = True
    ) -> Dict[str, Any]:
        """
        Convert model to dictionary with optional filtering.

        Args:
            exclude_none: Whether to exclude None values
            exclude_sensitive: Whether to exclude sensitive fields

        Returns:
            Dictionary representation of the model
        """
        # Use Pydantic v2 method if available, fallback to v1
        if hasattr(self, "model_dump"):
            data = self.model_dump(exclude_none=exclude_none)
        else:
            data = self.dict(exclude_none=exclude_none)

        if exclude_sensitive:
            sensitive_fields = ["hashed_password", "password", "token", "secret"]
            for field in sensitive_fields:
                data.pop(field, None)

        return data

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def soft_delete(self) -> None:
        """Perform soft delete by setting deletion flags."""
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        self.update_timestamp()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        self.update_timestamp()

    @property
    def is_available(self) -> bool:
        """Check if the record is available (active and not deleted)."""
        return self.is_active and not self.is_deleted
