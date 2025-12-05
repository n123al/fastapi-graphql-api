"""
User data models and schemas.

This module defines the Pydantic models for user-related data, providing
validation and serialization for user information throughout the application.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.data.models.base import BaseDataModel


class UserProfile(BaseModel):
    """
    User profile information model.

    This class encapsulates optional user profile data that enhances
    the basic user information with personal details.
    """

    first_name: Optional[str] = Field(
        default=None, max_length=100, description="User's first name"
    )
    last_name: Optional[str] = Field(
        default=None, max_length=100, description="User's last name"
    )
    bio: Optional[str] = Field(
        default=None, max_length=1000, description="User biography"
    )
    full_name: Optional[str] = None  # Added this field
    avatar_url: Optional[str] = Field(
        default=None, description="URL to user's avatar image"
    )
    phone_number: Optional[str] = Field(default=None, description="User's phone number")
    date_of_birth: Optional[datetime] = Field(
        default=None, description="User's date of birth"
    )


class UserPreferences(BaseModel):
    """
    User preferences model.

    This class defines user-configurable preferences for application
    behavior and appearance.
    """

    theme: str = Field(default="light", description="UI theme preference")
    language: str = Field(default="en", description="Preferred language code")
    timezone: str = Field(default="UTC", description="User's timezone")
    notifications_enabled: bool = Field(
        default=True, description="Whether notifications are enabled"
    )
    email_notifications: bool = Field(
        default=True, description="Whether email notifications are enabled"
    )
    push_notifications: bool = Field(
        default=False, description="Whether push notifications are enabled"
    )


class User(BaseDataModel):
    """
    User data model.

    This class represents a user in the system, containing all user-related
    information including authentication, profile, and preferences.
    """

    # Basic identification
    username: str = Field(
        ..., min_length=3, max_length=50, description="Unique username"
    )
    email: EmailStr = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Hashed password for authentication")

    # Profile and preferences
    profile: UserProfile = Field(
        default_factory=UserProfile, description="User profile information"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences, description="User preferences"
    )

    # Status and verification
    email_verified: bool = Field(default=False, description="Whether email is verified")
    is_superuser: bool = Field(
        default=False, description="Whether user has superuser privileges"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Last login timestamp"
    )

    # Security fields
    login_attempts: int = Field(
        default=0, description="Number of failed login attempts"
    )
    failed_login_attempts: int = Field(
        default=0, description="Number of failed login attempts (compat)"
    )
    locked_until: Optional[datetime] = Field(
        default=None, description="Account lock expiration time"
    )

    # Relationships (stored as IDs)
    role_ids: List[str] = Field(default_factory=list, description="User's role IDs")
    group_ids: List[str] = Field(default_factory=list, description="User's group IDs")
    permission_ids: List[str] = Field(
        default_factory=list, description="User's direct permission IDs"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name from profile."""
        if self.profile and self.profile.full_name:
            return self.profile.full_name
        return self.profile.first_name or self.profile.last_name or ""

    def get_full_name(self) -> str:
        """Get full name with priority logic."""
        if self.profile and self.profile.full_name:
            return self.profile.full_name
        if self.profile.first_name and self.profile.last_name:
            return f"{self.profile.first_name} {self.profile.last_name}"
        return self.profile.first_name or self.profile.last_name or ""

    @property
    def is_locked(self) -> bool:
        """Check if user account is currently locked."""
        if self.locked_until:
            return datetime.now(timezone.utc) < self.locked_until
        return False

    @property
    def display_name(self) -> str:
        """Get the display name for the user."""
        return self.full_name if self.profile.first_name else self.username

    def is_member_of(self, group_name: str) -> bool:
        """
        Check if user is member of specific group.

        Args:
            group_name: Name of the group to check

        Returns:
            True if user is member of the group, False otherwise
        """
        # Simplified implementation
        return False

    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock the user account for specified duration.

        Args:
            duration_minutes: Duration in minutes to lock the account
        """
        self.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=duration_minutes
        )
        self.update_timestamp()

    def unlock_account(self) -> None:
        """Unlock the user account."""
        self.locked_until = None
        self.login_attempts = 0
        self.update_timestamp()

    async def increment_login_attempts(self) -> None:
        """Increment failed login attempts counter."""
        self.login_attempts += 1
        if self.login_attempts >= 5:  # Lock after 5 attempts
            self.lock_account()
        self.update_timestamp()

        # Persist to database
        from app.data.repositories import UserRepository

        if hasattr(self, "id") and self.id:
            repo = UserRepository()
            await repo.update(
                self.id,
                {
                    "login_attempts": self.login_attempts,
                    "locked_until": self.locked_until,
                },
            )

    async def reset_login_attempts(self) -> None:
        """Reset failed login attempts counter."""
        self.login_attempts = 0
        self.unlock_account()

        # Persist to database
        from app.data.repositories import UserRepository

        if hasattr(self, "id") and self.id:
            repo = UserRepository()
            await repo.update(self.id, {"login_attempts": 0, "locked_until": None})

    def to_response_dict(self) -> Dict[str, Any]:
        """
        Convert user to response dictionary (excluding sensitive data).

        Returns:
            Dictionary with safe user data for API responses
        """
        return {
            "id": getattr(self, "id", None),
            "username": self.username,
            "email": self.email,
            "profile": self.profile.dict(),
            "preferences": self.preferences.dict(),
            "email_verified": self.email_verified,
            "is_superuser": self.is_superuser,
            "display_name": self.display_name,
            "full_name": self.full_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "last_login": self.last_login,
            "role_ids": self.role_ids,
            "group_ids": self.group_ids,
        }

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(username='{self.username}', email='{self.email}')>"

    def __str__(self) -> str:
        """String representation of the user."""
        return self.display_name
