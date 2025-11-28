"""
Authentication service implementing business logic for user authentication.

This module provides comprehensive authentication functionality including
user login, logout, token management, password handling, and account
security features.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast

from app.core import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    settings,
    verify_password,
)
from app.data import User, UserRepository
from app.services.base import BaseService


class AuthenticationService(BaseService[User]):
    """
    Authentication service handling user login, tokens, and security.

    This service manages the complete authentication flow including:
    - User credential validation
    - Token generation and validation
    - Account security (locking, failed attempts)
    - Session management
    - Password handling

    Attributes:
        user_repository: Repository for user data operations
        max_login_attempts: Maximum failed login attempts before lockout
        lockout_duration_minutes: Duration of account lockout

    Example:
        ```python
        auth_service = AuthenticationService(user_repository)
        user = await auth_service.authenticate_user("user@example.com", "password123")
        tokens = await auth_service.generate_tokens(user)
        ```
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize the authentication service.

        Args:
            user_repository: Repository for user data operations
        """
        super().__init__(user_repository, "AuthenticationService")
        self.user_repository: UserRepository = user_repository
        self.max_login_attempts = getattr(settings, "MAX_LOGIN_ATTEMPTS", 5)
        self.lockout_duration_minutes = getattr(
            settings, "LOCKOUT_DURATION_MINUTES", 30
        )

    async def authenticate_user(self, identifier: str, password: str) -> User:
        """
        Authenticate user with email/username and password.

        Args:
            identifier: User's email address or username
            password: User's password

        Returns:
            Authenticated user object

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If input validation fails
        """
        # Validate input
        if not identifier or not password:
            raise ValidationError("Both identifier and password are required")

        # Find user by email or username
        user = await self._find_user_by_identifier(identifier)
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Check account status
        self._check_account_status(user)

        # Verify password
        if not verify_password(password, user.hashed_password):
            await self._handle_failed_login(user)
            raise AuthenticationError("Invalid credentials")

        # Successful login - reset failed attempts
        await self._handle_successful_login(user)

        return user

    async def register_user(self, registration_data: Dict[str, Any]) -> User:
        """
        Register a new user account.

        Args:
            registration_data: User registration data containing:
                - username: Unique username
                - email: Email address
                - password: Plain text password
                - full_name: Optional full name
                - additional profile data

        Returns:
            Newly created user object

        Raises:
            ValidationError: If registration data is invalid
            ConflictError: If username/email already exists
        """
        # Validate required fields
        required_fields = ["username", "email", "password"]
        self._validate_required_fields(registration_data, required_fields)

        # Check for existing user
        username = str(registration_data.get("username"))
        email = str(registration_data.get("email"))
        await self._check_user_exists(username, email)

        # Hash password
        password_hash = get_password_hash(registration_data["password"])

        # Prepare user data
        user_data = {
            "username": registration_data["username"],
            "email": registration_data["email"],
            "hashed_password": password_hash,
            "profile": {
                "full_name": registration_data.get("full_name", ""),
                "bio": registration_data.get("bio", ""),
                "avatar_url": registration_data.get("avatar_url", ""),
            },
            "preferences": {
                "theme": registration_data.get("theme", "light"),
                "language": registration_data.get("language", "en"),
                "timezone": registration_data.get("timezone", "UTC"),
            },
            "is_active": True,
            "is_verified": False,
            "failed_login_attempts": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Create user
        user = User(**user_data)
        created_user = await self.user_repository.create(user)

        self._log_operation(
            "user_registered",
            {
                "user_id": created_user.id,
                "username": created_user.username,
                "email": created_user.email,
            },
        )

        return created_user

    async def generate_tokens(self, user: User) -> Dict[str, Any]:
        """
        Generate access and refresh tokens for authenticated user.

        Args:
            user: Authenticated user object

        Returns:
            Dictionary containing access_token, refresh_token, and token info

        Example:
            ```python
            tokens = await auth_service.generate_tokens(user)
            # Returns: {
            #     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            #     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            #     "token_type": "bearer",
            #     "expires_in": 1800
            # }
            ```
        """
        # Create token payload
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
        }

        # Generate tokens
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def login(self, identifier: str, password: str) -> Dict[str, Any]:
        user = await self.authenticate_user(identifier, password)
        return await self.generate_tokens(user)

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token and token information

        Raises:
            AuthenticationError: If refresh token is invalid or expired
        """
        try:
            # Decode and validate refresh token
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            # Get user from token
            user_id = payload.get("sub")
            user = await self.get_by_id(str(user_id))

            if not user or not user.is_active:
                raise AuthenticationError("User account is inactive")

            # Generate new access token
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            }

            new_access_token = create_access_token(data=token_data)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError("Invalid or expired refresh token")

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User's unique identifier
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password was changed successfully

        Raises:
            AuthenticationError: If current password is incorrect
            ValidationError: If new password is invalid
        """
        # Get user
        user = await self.get_by_id(user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        from app.core.utils import validate_password as validate_pwd

        is_valid, errors = validate_pwd(new_password)
        if not is_valid:
            raise ValidationError(f"Invalid password: {', '.join(errors)}")

        # Hash and update password
        new_password_hash = get_password_hash(new_password)
        updated_user = await self.user_repository.update(
            user_id,
            {
                "hashed_password": new_password_hash,
                "password_changed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

        if updated_user:
            self._log_operation(
                "password_changed",
                {
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return True

        return False

    async def set_password_with_token(self, token: str, new_password: str) -> bool:
        try:
            payload = decode_token(token)
            token_type = payload.get("type")
            if token_type != "set_password":  # nosec
                raise AuthenticationError("Invalid token type")
            user_id = str(payload.get("sub"))
            if not user_id:
                raise AuthenticationError("Invalid token")
            from app.core.utils import validate_password as validate_pwd

            is_valid, errors = validate_pwd(new_password)
            if not is_valid:
                raise ValidationError(f"Invalid password: {', '.join(errors)}")
            new_hash = get_password_hash(new_password)
            updated_user = await self.user_repository.update(
                user_id,
                {
                    "hashed_password": new_hash,
                    "is_verified": True,
                    "password_changed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            if updated_user:
                self._log_operation(
                    "password_set_via_token",
                    {
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                return True
            return False
        except Exception as e:
            if isinstance(e, (AuthenticationError, ValidationError)):
                raise
            raise AuthenticationError("Invalid or expired token")

    async def reset_failed_attempts(self, user_id: str) -> bool:
        """
        Reset failed login attempts for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if reset was successful
        """
        updated_user = await self.user_repository.update(
            user_id,
            {
                "failed_login_attempts": 0,
                "locked_until": None,
                "updated_at": datetime.now(timezone.utc),
            },
        )

        return updated_user is not None

    async def _find_user_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Find user by email or username.

        Args:
            identifier: Email address or username

        Returns:
            User object if found, None otherwise
        """
        # Try to find by email first
        user = await self.user_repository.get_by_email(identifier)
        if user:
            return user

        # Try to find by username
        return await self.user_repository.get_by_username(identifier)

    def _check_account_status(self, user: User) -> None:
        """
        Check if user account is in good standing for authentication.

        Args:
            user: User object to check

        Raises:
            AuthenticationError: If account is locked or inactive
        """
        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AuthenticationError("Account is locked")

    async def _handle_failed_login(self, user: User) -> None:
        """
        Handle failed login attempt.

        Args:
            user: User who failed authentication
        """
        # Increment failed attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        # Lock account if max attempts reached
        if user.failed_login_attempts >= self.max_login_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.lockout_duration_minutes
            )

        # Update user record
        await self.user_repository.update(
            str(user.id),
            {
                "failed_login_attempts": user.failed_login_attempts,
                "locked_until": user.locked_until,
                "last_failed_login": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

    async def _handle_successful_login(self, user: User) -> None:
        """
        Handle successful login.

        Args:
            user: User who successfully authenticated
        """
        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None

        # Update user record
        await self.user_repository.update(
            str(user.id),
            {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

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
