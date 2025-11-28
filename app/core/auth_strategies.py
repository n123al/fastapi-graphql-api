from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError, TokenError
from app.data.models.user import User
from app.data.repositories import UserRepository


class IPasswordManager(ABC):
    """Interface for password management."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        pass


class PasswordManager(IPasswordManager):
    """Password manager with stable default and optional bcrypt support."""

    def __init__(self) -> None:
        # Prefer pbkdf2 for hashing to avoid platform-specific bcrypt issues
        # Still support verifying existing bcrypt hashes
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt"],
            deprecated="auto",
            default="pbkdf2_sha256",
        )

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        hashed: str = self.pwd_context.hash(password)
        return hashed

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        ok: bool = self.pwd_context.verify(plain_password, hashed_password)
        return ok


class ITokenManager(ABC):
    """Interface for JWT token management."""

    @abstractmethod
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token."""
        pass

    @abstractmethod
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token."""
        pass

    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a token."""
        pass

    @abstractmethod
    def create_action_token(
        self, data: Dict[str, Any], minutes: int, token_type: str
    ) -> str:
        pass


class TokenManager(ITokenManager):
    """JWT token manager."""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expire_minutes
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.refresh_token_expire_minutes
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a token."""
        try:
            payload = cast(
                Dict[str, Any],
                jwt.decode(token, self.secret_key, algorithms=[self.algorithm]),
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenError("Token has expired")
        except jwt.PyJWTError as e:
            raise TokenError(f"Invalid token: {str(e)}")

    def create_action_token(
        self, data: Dict[str, Any], minutes: int, token_type: str
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        to_encode.update({"exp": expire, "type": token_type})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


class IAuthenticationStrategy(ABC):
    """Interface for authentication strategies."""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> User:
        """Authenticate user with given credentials."""
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> User:
        """Validate authentication token."""
        pass


class UsernamePasswordAuthStrategy(IAuthenticationStrategy):
    """Username/Password authentication strategy."""

    def __init__(self) -> None:
        self._user_repository: Optional[UserRepository] = None
        self._password_manager: Optional[PasswordManager] = None
        self._token_manager: Optional[TokenManager] = None

    @property
    def user_repository(self) -> UserRepository:
        """Lazy load user repository to avoid circular imports."""
        if self._user_repository is None:
            from app.data.repositories import UserRepository

            self._user_repository = UserRepository()
        return self._user_repository

    @property
    def password_manager(self) -> PasswordManager:
        """Lazy load password manager."""
        if self._password_manager is None:
            self._password_manager = PasswordManager()
        return self._password_manager

    @property
    def token_manager(self) -> TokenManager:
        """Lazy load token manager."""
        if self._token_manager is None:
            self._token_manager = TokenManager()
        return self._token_manager

    async def authenticate(self, credentials: Dict[str, Any]) -> User:
        """Authenticate user with username/email and password."""
        identifier = credentials.get("username") or credentials.get("email")
        password = credentials.get("password")

        if not identifier or not password:
            raise AuthenticationError("Username/email and password are required")

        # Find user by email or username
        user: Optional[User] = await self.user_repository.get_by_email_or_username(
            identifier
        )
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Check if account is locked
        if user.is_locked:
            raise AuthenticationError(
                "Account is locked due to too many failed attempts"
            )

        # Verify password
        if not self.password_manager.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            await user.increment_login_attempts()
            raise AuthenticationError("Invalid credentials")

        # Reset login attempts on successful authentication
        await user.reset_login_attempts()

        if user is None:
            raise AuthenticationError("User not found")
        return user

    async def validate_token(self, token: str) -> User:
        """Validate JWT token and return user."""
        try:
            payload = self.token_manager.decode_token(token)

            if payload.get("type") != "access":
                raise AuthenticationError("Invalid token type")

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token")

            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            return user

        except TokenError as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")


class EmailAuthStrategy(IAuthenticationStrategy):
    """Email-based authentication strategy."""

    def __init__(self) -> None:
        self._user_repository: Optional[UserRepository] = None
        self._token_manager: Optional[TokenManager] = None

    @property
    def user_repository(self) -> UserRepository:
        """Lazy load user repository to avoid circular imports."""
        if self._user_repository is None:
            from app.data.repositories import UserRepository

            self._user_repository = UserRepository()
        return self._user_repository

    @property
    def token_manager(self) -> TokenManager:
        """Lazy load token manager."""
        if self._token_manager is None:
            self._token_manager = TokenManager()
        return self._token_manager

    async def authenticate(self, credentials: Dict[str, Any]) -> User:
        """Authenticate user with email (passwordless or with magic link)."""
        email = credentials.get("email")
        magic_token = credentials.get("magic_token")

        if not email:
            raise AuthenticationError("Email is required")

        user: Optional[User] = await self.user_repository.get_by_email(email)
        if not user:
            raise AuthenticationError("User not found")

        # For magic token authentication
        if magic_token:
            try:
                payload = self.token_manager.decode_token(magic_token)
                if payload.get("email") != email:
                    raise AuthenticationError("Invalid magic token")
                if user is None:
                    raise AuthenticationError("User not found")
                return user
            except TokenError:
                raise AuthenticationError("Invalid magic token")

        # For passwordless authentication, you might send an email here
        # This is a simplified version
        if user is None:
            raise AuthenticationError("User not found")
        return user

    async def validate_token(self, token: str) -> User:
        """Validate token and return user."""
        # Reuse the same token validation logic
        username_strategy = UsernamePasswordAuthStrategy()
        return await username_strategy.validate_token(token)


class AuthenticationContext:
    """Context class for authentication strategies."""

    def __init__(self, strategy: IAuthenticationStrategy) -> None:
        self.strategy = strategy

    async def authenticate(self, credentials: Dict[str, Any]) -> User:
        """Authenticate using the current strategy."""
        return await self.strategy.authenticate(credentials)

    async def validate_token(self, token: str) -> User:
        """Validate token using the current strategy."""
        return await self.strategy.validate_token(token)

    def set_strategy(self, strategy: IAuthenticationStrategy) -> None:
        """Change authentication strategy."""
        self.strategy = strategy


class AuthenticationStrategyFactory:
    """Factory for creating authentication strategies."""

    @staticmethod
    def create_strategy(strategy_type: str) -> IAuthenticationStrategy:
        """Create authentication strategy based on type."""
        strategies = {
            "username_password": UsernamePasswordAuthStrategy,
            "email": EmailAuthStrategy,
        }

        strategy_class = strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown authentication strategy: {strategy_type}")

        return strategy_class()

    @staticmethod
    def get_available_strategies() -> List[str]:
        """Get list of available authentication strategies."""
        return ["username_password", "email"]


class AuthorizationService:
    def __init__(self) -> None:
        from app.data.repositories import (
            PermissionRepository,
            RoleRepository,
            UserRepository,
        )

        self.user_repository = UserRepository()
        self.role_repository = RoleRepository()
        self.permission_repository = PermissionRepository()

    async def has_permission(self, user: User, permission_name: str) -> bool:
        if user.is_superuser:
            return True
        perm = await self.permission_repository.get_by_name(permission_name)
        if not perm:
            return False
        if perm.id in getattr(user, "permission_ids", []):
            return True
        for role_id in getattr(user, "role_ids", []):
            role = await self.role_repository.get_by_id(role_id)
            if role and perm.id in getattr(role, "permission_ids", []):
                return True
        return False

    async def has_role(self, user: User, role_name: str) -> bool:
        if user.is_superuser:
            return True
        for role_id in getattr(user, "role_ids", []):
            role = await self.role_repository.get_by_id(role_id)
            if role and role.name == role_name:
                return True
        return False

    async def has_any_permission(self, user: User, permissions: List[str]) -> bool:
        for name in permissions:
            if await self.has_permission(user, name):
                return True
        return False

    async def has_all_permissions(self, user: User, permissions: List[str]) -> bool:
        for name in permissions:
            if not await self.has_permission(user, name):
                return False
        return True

    async def get_user_permissions(self, user_id: str) -> List[str]:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []
        names = []
        for perm_id in getattr(user, "permission_ids", []):
            p = await self.permission_repository.get_by_id(perm_id)
            if p:
                names.append(p.name)
        for role_id in getattr(user, "role_ids", []):
            role = await self.role_repository.get_by_id(role_id)
            if role:
                for perm_id in getattr(role, "permission_ids", []):
                    p = await self.permission_repository.get_by_id(perm_id)
                    if p:
                        names.append(p.name)
        return list(set(names))

    async def get_user_roles(self, user_id: str) -> List[str]:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []
        names = []
        for role_id in getattr(user, "role_ids", []):
            role = await self.role_repository.get_by_id(role_id)
            if role:
                names.append(role.name)
        return names
