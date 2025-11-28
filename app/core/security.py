from typing import Optional, Dict, Any, Callable
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings


class SecurityManager:
    """Security manager for authentication and authorization."""
    
    def __init__(self) -> None:
        self.security = HTTPBearer()
        from app.core.auth_strategies import AuthenticationStrategyFactory, AuthenticationContext
        self._strategy_factory: Optional[AuthenticationStrategyFactory] = None
        self._auth_context: Optional[AuthenticationContext] = None
    
    @property
    def strategy_factory(self) -> Any:
        """Lazy load strategy factory to avoid circular imports."""
        if self._strategy_factory is None:
            from app.core.auth_strategies import AuthenticationStrategyFactory
            self._strategy_factory = AuthenticationStrategyFactory()
        return self._strategy_factory
    
    def get_auth_context(self, strategy_type: str = "username_password") -> Any:
        """Get authentication context with specified strategy."""
        strategy = self.strategy_factory.create_strategy(strategy_type)
        from app.core.auth_strategies import AuthenticationContext
        return AuthenticationContext(strategy)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Any:
        """Get current user from JWT token."""
        token = credentials.credentials
        
        # Use default authentication strategy
        auth_context = self.get_auth_context()
        
        try:
            user = await auth_context.validate_token(token)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_active_user(self, current_user: Any = Depends(get_current_user)) -> Any:
        """Get current active user."""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return current_user
    
    def require_permission(self, permission: str) -> Callable[..., Any]:
        """Dependency to require specific permission."""
        async def permission_checker(current_user: Any = Depends(self.get_current_user)) -> Any:
            from app.core.auth_strategies import AuthorizationService
            auth_service = AuthorizationService()
            ok = await auth_service.has_permission(current_user, permission)
            if not ok:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            return current_user
        return permission_checker
    
    def require_role(self, role: str) -> Callable[..., Any]:
        """Dependency to require specific role."""
        async def role_checker(current_user: Any = Depends(self.get_current_user)) -> Any:
            from app.core.auth_strategies import AuthorizationService
            auth_service = AuthorizationService()
            ok = await auth_service.has_role(current_user, role)
            if not ok:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )
            return current_user
        return role_checker
    
    def require_any_permission(self, permissions: list[str]) -> Callable[..., Any]:
        """Dependency to require any of the specified permissions."""
        async def permission_checker(current_user: Any = Depends(self.get_current_user)) -> Any:
            from app.core.auth_strategies import AuthorizationService
            auth_service = AuthorizationService()
            ok = await auth_service.has_any_permission(current_user, permissions)
            if not ok:
                perm_list = ", ".join(permissions)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {perm_list}"
                )
            return current_user
        return permission_checker
    
    def require_all_permissions(self, permissions: list[str]) -> Callable[..., Any]:
        """Dependency to require all specified permissions."""
        async def permission_checker(current_user: Any = Depends(self.get_current_user)) -> Any:
            from app.core.auth_strategies import AuthorizationService
            auth_service = AuthorizationService()
            ok = await auth_service.has_all_permissions(current_user, permissions)
            if not ok:
                perm_list = ", ".join(permissions)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"All these permissions required: {perm_list}"
                )
            return current_user
        return permission_checker


# Create global security manager instance
security_manager = SecurityManager()


# Re-export commonly used dependencies
get_current_user = security_manager.get_current_user
get_current_active_user = security_manager.get_current_active_user

# Add password management functions
def get_password_hash(password: str) -> str:
    """Get password hash using the security manager."""
    from app.core.auth_strategies import PasswordManager
    password_manager = PasswordManager()
    return password_manager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using the security manager."""
    from app.core.auth_strategies import PasswordManager
    password_manager = PasswordManager()
    return password_manager.verify_password(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Create access token using the security manager."""
    from app.core.auth_strategies import TokenManager
    token_manager = TokenManager()
    return token_manager.create_access_token(data)

def create_refresh_token(data: dict) -> str:
    """Create refresh token using the security manager."""
    from app.core.auth_strategies import TokenManager
    token_manager = TokenManager()
    return token_manager.create_refresh_token(data)

def decode_token(token: str) -> dict:
    """Decode token using the security manager."""
    from app.core.auth_strategies import TokenManager
    token_manager = TokenManager()
    return token_manager.decode_token(token)

def create_set_password_token(data: dict) -> str:
    from app.core.auth_strategies import TokenManager
    token_manager = TokenManager()
    return token_manager.create_action_token(data, settings.SET_PASSWORD_TOKEN_EXPIRE_MINUTES, "set_password")