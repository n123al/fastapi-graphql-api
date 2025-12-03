"""
Core package containing application framework components and shared utilities.

This package provides the foundational components for the application including:
- Configuration management and settings
- Security utilities and authentication strategies
- Exception handling and error management
- Database connection management
- Shared interfaces and base classes
- Common utilities and helpers

The core package serves as the foundation layer that other packages depend on,
providing stable interfaces and shared functionality throughout the application.
"""

# Authentication Strategies
from app.core.auth_strategies import (
    AuthenticationContext,
    AuthenticationStrategyFactory,
    AuthorizationService,
    EmailAuthStrategy,
    IAuthenticationStrategy,
    UsernamePasswordAuthStrategy,
)

# Configuration
from app.core.config import Settings, settings

# Constants
from app.core.constants import API_RATE_LIMITS, DEFAULT_ROLES, PERMISSIONS

# Exceptions
from app.core.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseConnectionError,
    NotFoundError,
    TokenError,
    ValidationError,
)

# Database
from app.core.motor_database import motor_db_manager

# Security
from app.core.security import (
    SecurityManager,
    create_access_token,
    create_refresh_token,
    create_set_password_token,
    decode_token,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    security_manager,
    verify_password,
)

__all__ = [
    # Configuration
    "Settings",
    "settings",
    # Security
    "SecurityManager",
    "security_manager",
    "get_current_user",
    "get_current_active_user",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_set_password_token",
    "decode_token",
    # Authentication Strategies
    "IAuthenticationStrategy",
    "UsernamePasswordAuthStrategy",
    "EmailAuthStrategy",
    "AuthenticationStrategyFactory",
    "AuthenticationContext",
    "AuthorizationService",
    # Exceptions
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "TokenError",
    "DatabaseConnectionError",
    # Database
    "motor_db_manager",
    # Constants
    "PERMISSIONS",
    "DEFAULT_ROLES",
    "API_RATE_LIMITS",
]
