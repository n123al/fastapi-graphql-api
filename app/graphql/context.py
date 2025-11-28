"""
GraphQL context implementation for authorization and request handling.

This module provides the GraphQL context class that encapsulates request-scoped
data and authorization functionality for GraphQL resolvers.
"""

from typing import Optional, Any
from fastapi import Request
from app.core.motor_database import MotorDatabaseManager
from app.core.security import SecurityManager
from app.data.models.user import User


class GraphQLContext:
    """
    GraphQL context class that provides request-scoped data and authorization functionality.
    
    This class encapsulates the GraphQL request context, providing access to:
    - Database managers and connections
    - Security and authentication services
    - Current user information
    - Authorization checking functionality
    
    Attributes:
        motor_db_manager: MongoDB Motor database manager instance
        security_manager: Security manager for authentication and authorization
        _current_user: Cached current user for the request
    """
    
    def __init__(
        self,
        motor_db_manager: MotorDatabaseManager,
        security_manager: SecurityManager,
        request: Optional[Request] = None
    ):
        """
        Initialize the GraphQL context.
        
        Args:
            motor_db_manager: MongoDB Motor database manager instance
            security_manager: Security manager for authentication and authorization
            request: Optional FastAPI request object
        """
        self.motor_db_manager = motor_db_manager
        self.security_manager = security_manager
        self.request = request
        self._current_user: Optional[User] = None
        self._auth_context = None
        
        # Initialize authentication context
        from app.core.auth_strategies import AuthenticationContext, UsernamePasswordAuthStrategy
        self._auth_context = AuthenticationContext(UsernamePasswordAuthStrategy())
    
    async def get_current_user(self) -> Optional[User]:
        """
        Get the current authenticated user from the request.
        
        Returns:
            The current User object if authenticated, None otherwise
            
        Note:
            This method extracts JWT token from Authorization header and validates it.
        """
        if self._current_user is None and self.request:
            try:
                # Extract Authorization header
                auth_header = self.request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return None
                
                # Extract token
                token = auth_header.split(" ")[1]  # Remove "Bearer " prefix
                
                # Validate token using authentication context
                if self._auth_context:
                    self._current_user = await self._auth_context.validate_token(token)
                
            except Exception:
                # If authentication fails, return None
                self._current_user = None
        
        return self._current_user
    
    async def has_permission(self, permission: str) -> bool:
        """
        Check if the current user has a specific permission.
        """
        user = await self.get_current_user()
        if not user:
            return False
        from app.core.auth_strategies import AuthorizationService
        auth_service = AuthorizationService()
        return await auth_service.has_permission(user, permission)
    
    async def has_role(self, role: str) -> bool:
        """
        Check if the current user has a specific role.
        """
        user = await self.get_current_user()
        if not user:
            return False
        from app.core.auth_strategies import AuthorizationService
        auth_service = AuthorizationService()
        return await auth_service.has_role(user, role)
    
    async def has_any_permission(self, permissions: list[str]) -> bool:
        """
        Check if the current user has any of the specified permissions.
        """
        for perm in permissions:
            if await self.has_permission(perm):
                return True
        return False
    
    async def has_all_permissions(self, permissions: list[str]) -> bool:
        """
        Check if the current user has all of the specified permissions.
        """
        for perm in permissions:
            if not await self.has_permission(perm):
                return False
        return True
    
    @property
    def is_authenticated(self) -> bool:
        """
        Check if there is an authenticated user in the current request.
        """
        return self._current_user is not None
    
    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access for backward compatibility.
        
        Args:
            key: The key to access
            
        Returns:
            The value associated with the key
            
        Raises:
            KeyError: If the key doesn't exist
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' not found in context")
    
    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the context.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return hasattr(self, key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context with a default fallback.
        
        Args:
            key: The key to access
            default: Default value if key doesn't exist
            
        Returns:
            The value associated with the key, or default if not found
        """
        try:
            return self[key]
        except KeyError:
            return default