"""
Services package providing business logic layer for the application.

This package contains all service implementations following a clean architecture
pattern with clear separation of concerns and business logic encapsulation.
"""

# Authentication service
from app.services.auth import AuthenticationService

# Base service classes
from app.services.base import BaseService

# User service
from app.services.user import UserService

__all__ = [
    # Base classes
    "BaseService",
    # Service implementations
    "AuthenticationService",
    "UserService",
]
