"""
User service implementing business logic for user management.

This module provides comprehensive user management functionality including
user creation, updates, profile management, and user-related operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core import (
    ValidationError, 
    NotFoundError, 
    ConflictError,
    get_password_hash,
    verify_password,
    settings
)
from app.data import User, UserRepository
from app.services.base import BaseService


class UserService(BaseService[User]):
    """
    User service handling user management operations.
    
    This service manages all user-related business logic including:
    - User creation and registration
    - Profile management
    - User updates and modifications
    - User search and filtering
    - Account status management
    
    Attributes:
        user_repository: Repository for user data operations
        default_page_size: Default number of users per page
        max_page_size: Maximum allowed users per page
    
    Example:
        ```python
        user_service = UserService(user_repository)
        user = await user_service.create_user({
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password"
        })
        ```
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the user service.
        
        Args:
            user_repository: Repository for user data operations
        """
        super().__init__(user_repository, "UserService")
        self.user_repository: UserRepository = user_repository
        self.default_page_size = 20
        self.max_page_size = 100
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user with validation and business logic.
        
        Args:
            user_data: User creation data containing:
                - username: Unique username
                - email: Email address
                - password: Plain text password
                - full_name: Optional full name
                - additional profile data
                
        Returns:
            Newly created user object
            
        Raises:
            ValidationError: If user data is invalid
            ConflictError: If username/email already exists
        """
        # Validate required fields
        required_fields = ["username", "email", "password"]
        self._validate_required_fields(user_data, required_fields)
        
        # Validate username format
        from app.core.utils import validate_username
        if not validate_username(user_data["username"]):
            raise ValidationError("Invalid username format")
        
        # Validate email format
        from app.core.utils import validate_email
        if not validate_email(user_data["email"]):
            raise ValidationError("Invalid email format")
        
        # Validate password strength
        from app.core.utils import validate_password
        is_valid, errors = validate_password(user_data["password"])
        if not is_valid:
            raise ValidationError(f"Invalid password: {', '.join(errors)}")
        
        # Check for existing user
        await self._check_user_exists(user_data["username"], user_data["email"])
        
        # Hash password
        password_hash = get_password_hash(user_data["password"])
        
        # Prepare user data
        user_data_for_creation = {
            "username": user_data["username"].lower().strip(),
            "email": user_data["email"].lower().strip(),
            "hashed_password": password_hash,
            "profile": {
                "full_name": user_data.get("full_name", "").strip(),
                "bio": user_data.get("bio", "").strip(),
                "avatar_url": user_data.get("avatar_url", "").strip(),
                "phone": user_data.get("phone", "").strip(),
                "date_of_birth": user_data.get("date_of_birth"),
                "location": user_data.get("location", "").strip()
            },
            "preferences": {
                "theme": user_data.get("theme", "light"),
                "language": user_data.get("language", "en"),
                "timezone": user_data.get("timezone", "UTC"),
                "notifications": {
                    "email": user_data.get("email_notifications", True),
                    "push": user_data.get("push_notifications", True),
                    "sms": user_data.get("sms_notifications", False)
                }
            },
            "is_active": True,
            "is_verified": False,
            "is_superuser": False,
            "failed_login_attempts": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Create user
        user = User(**user_data_for_creation)
        created_user = await self.repository.create(user)
        
        self._log_operation("user_created", {
            "user_id": created_user.id,
            "username": created_user.username,
            "email": created_user.email
        })
        
        return created_user
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user information with validation.
        
        Args:
            user_id: User's unique identifier
            update_data: Data to update (username, email, profile, etc.)
            
        Returns:
            Updated user object if successful, None otherwise
            
        Raises:
            ValidationError: If update data is invalid
            ConflictError: If username/email conflicts with existing users
        """
        # Get existing user
        existing_user = await self.get_by_id(user_id)
        
        # Validate and process updates
        processed_updates = {}
        
        # Handle username update
        if "username" in update_data:
            new_username = update_data["username"].lower().strip()
            if new_username != existing_user.username:
                from app.core.utils import validate_username
                if not validate_username(new_username):
                    raise ValidationError("Invalid username format")
                
                # Check if new username is available
                username_conflict = await self.user_repository.get_by_username(new_username)
                if username_conflict and username_conflict.id != user_id:
                    raise ConflictError("Username already taken")
                
                processed_updates["username"] = new_username
        
        # Handle email update
        if "email" in update_data:
            new_email = update_data["email"].lower().strip()
            if new_email != existing_user.email:
                from app.core.utils import validate_email
                if not validate_email(new_email):
                    raise ValidationError("Invalid email format")
                
                # Check if new email is available
                email_conflict = await self.user_repository.get_by_email(new_email)
                if email_conflict and email_conflict.id != user_id:
                    raise ConflictError("Email already in use")
                
                processed_updates["email"] = new_email
        
        # Handle profile updates
        if "profile" in update_data:
            profile_updates = update_data["profile"]
            if isinstance(profile_updates, dict):
                # Merge with existing profile
                updated_profile = {**existing_user.profile.dict(), **profile_updates}
                processed_updates["profile"] = updated_profile
        
        # Handle preferences updates
        if "preferences" in update_data:
            preferences_updates = update_data["preferences"]
            if isinstance(preferences_updates, dict):
                # Merge with existing preferences
                updated_preferences = {**existing_user.preferences.dict(), **preferences_updates}
                processed_updates["preferences"] = updated_preferences
        
        # Handle other direct updates
        direct_fields = ["is_active", "is_verified", "is_superuser"]
        for field in direct_fields:
            if field in update_data:
                processed_updates[field] = update_data[field]
        
        # Add timestamp
        processed_updates["updated_at"] = datetime.now(timezone.utc)
        
        # Update user
        updated_user = await self.user_repository.update(user_id, processed_updates)
        
        if updated_user:
            self._log_operation("user_updated", {
                "user_id": user_id,
                "updates": list(processed_updates.keys())
            })
        
        return updated_user
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user profile information.
        
        Args:
            user_id: User's unique identifier
            profile_data: Profile data to update
            
        Returns:
            Updated user object if successful, None otherwise
        """
        return await self.update_user(user_id, {"profile": profile_data})
    
    async def update_user_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user preferences.
        
        Args:
            user_id: User's unique identifier
            preferences_data: Preferences data to update
            
        Returns:
            Updated user object if successful, None otherwise
        """
        return await self.update_user(user_id, {"preferences": preferences_data})
    
    async def search_users(self, query: str, limit: int = 20, filters: Optional[Dict[str, Any]] = None) -> List[User]:
        """
        Search users by username, email, or profile data.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            filters: Additional filter criteria
            
        Returns:
            List of matching users
        """
        if not query or not isinstance(query, str):
            return []
        
        # Normalize query
        query = query.lower().strip()
        
        # Basic search implementation - this would be enhanced with full-text search
        # in a production environment
        all_users = await self.get_all(limit=limit * 2)  # Get more to filter locally
        
        matching_users = []
        for user in all_users:
            # Search in username, email, and profile fields
            search_fields = [
                user.username,
                user.email,
                user.profile.full_name,
                user.profile.bio
            ]
            
            # Check if query matches any field
            if any(query in str(field).lower() for field in search_fields if field):
                matching_users.append(user)
                
                if len(matching_users) >= limit:
                    break
        
        return matching_users
    
    async def get_active_users(self, limit: int = 100, skip: int = 0) -> List[User]:
        """
        Get all active users.
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (for pagination)
            
        Returns:
            List of active users
        """
        return await self.get_all(limit=limit, skip=skip, is_active=True)
    
    async def get_verified_users(self, limit: int = 100, skip: int = 0) -> List[User]:
        """
        Get all verified users.
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (for pagination)
            
        Returns:
            List of verified users
        """
        return await self.get_all(limit=limit, skip=skip, is_verified=True)
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated user object if successful, None otherwise
        """
        return await self.update_user(user_id, {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc)
        })
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated user object if successful, None otherwise
        """
        return await self.update_user(user_id, {
            "is_active": True,
            "deactivated_at": None
        })
    
    async def verify_user(self, user_id: str) -> Optional[User]:
        """
        Mark user as verified.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated user object if successful, None otherwise
        """
        return await self.update_user(user_id, {
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc)
        })
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for dashboard/admin purposes.
        
        Returns:
            Dictionary containing user statistics
        """
        total_users = await self.count()
        active_users = await self.count(is_active=True)
        verified_users = await self.count(is_verified=True)
        superusers = await self.count(is_superuser=True)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "superusers": superusers,
            "inactive_users": total_users - active_users,
            "unverified_users": total_users - verified_users,
            "activation_rate": (active_users / total_users * 100) if total_users > 0 else 0,
            "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
        }
    
    async def _check_user_exists(self, username: str, email: str) -> None:
        """
        Check if username or email already exists.
        
        Args:
            username: Username to check
            email: Email to check
            
        Raises:
            ConflictError: If username or email already exists
        """
        # Check username
        existing_user = await self.user_repository.get_by_username(username)
        if existing_user:
            raise ConflictError("Username already exists")
        
        # Check email
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise ConflictError("Email already exists")

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.user_repository.get_by_username(username)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.user_repository.get_by_email(email)