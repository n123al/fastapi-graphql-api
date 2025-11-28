from typing import Any, Dict, Optional


class ApplicationError(Exception):
    """Base exception for the application."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    def __init__(
        self, message: str = "Authentication failed", code: str = "AUTH_FAILED"
    ):
        super().__init__(message, code)


class AuthorizationError(ApplicationError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied", code: str = "ACCESS_DENIED"):
        super().__init__(message, code)


class ValidationError(ApplicationError):
    """Raised when validation fails."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code)


class NotFoundError(ApplicationError):
    """Raised when a resource is not found."""

    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(message, code)


class ConflictError(ApplicationError):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(message, code)


class TokenError(ApplicationError):
    """Raised when token validation fails."""

    def __init__(self, message: str, code: str = "TOKEN_ERROR"):
        super().__init__(message, code)


class DatabaseError(ApplicationError):
    """Raised when database operation fails."""

    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        super().__init__(message, code)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")


class BusinessLogicError(ApplicationError):
    """Raised when business logic validation fails."""

    def __init__(self, message: str, code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(message, code)
