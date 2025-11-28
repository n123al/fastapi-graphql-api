"""
GraphQL authorization utilities and decorators.

This module provides authorization helpers specifically designed for GraphQL resolvers,
including decorators for permission and role-based access control.
"""

import functools
from typing import Any, Awaitable, Callable, Optional, TypeVar, cast

import strawberry
from strawberry.types import Info

from app.core.exceptions import AuthenticationError, AuthorizationError

CF = TypeVar("CF", bound=Callable[..., Awaitable[Any]])


def require_permission(permission: str) -> Callable[[CF], CF]:
    """
    Decorator to require a specific permission for a GraphQL resolver.

    Args:
        permission: The required permission in format "resource:action"

    Example:
        @require_permission("users:read")
        @strawberry.field
        async def users(self, info: Info) -> List[User]:
            return await get_users()
    """

    def decorator(resolver_func: CF) -> CF:
        @functools.wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from kwargs or args
            info = kwargs.get("info") or (args[1] if len(args) > 1 else None)

            if not info or not hasattr(info, "context"):
                raise AuthenticationError("GraphQL context not available")

            context = info.context
            from typing import cast as _cast

            from app.core.motor_database import MotorDatabaseManager
            from app.core.security import SecurityManager
            from app.graphql.context import GraphQLContext

            if isinstance(context, dict):
                ctx = GraphQLContext(
                    motor_db_manager=_cast(
                        MotorDatabaseManager, context.get("motor_db_manager")
                    ),
                    security_manager=_cast(
                        SecurityManager, context.get("security_manager")
                    ),
                    request=context.get("request"),
                )
            else:
                ctx = context

            # Check if user has the required permission
            if not await ctx.has_permission(permission):
                raise AuthorizationError(
                    f"Permission '{permission}' required to access this resource",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            # If authorized, proceed with the resolver
            return await resolver_func(*args, **kwargs)

        return cast(CF, wrapper)

    return decorator


def require_role(role: str) -> Callable[[CF], CF]:
    """
    Decorator to require a specific role for a GraphQL resolver.

    Args:
        role: The required role name

    Example:
        @require_role("admin")
        @strawberry.field
        async def system_stats(self, info: Info) -> SystemStats:
            return await get_system_stats()
    """

    def decorator(resolver_func: CF) -> CF:
        @functools.wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from kwargs or args
            info = kwargs.get("info") or (args[1] if len(args) > 1 else None)

            if not info or not hasattr(info, "context"):
                raise AuthenticationError("GraphQL context not available")

            context = info.context
            from typing import cast as _cast

            from app.core.motor_database import MotorDatabaseManager
            from app.core.security import SecurityManager
            from app.graphql.context import GraphQLContext

            if isinstance(context, dict):
                ctx = GraphQLContext(
                    motor_db_manager=_cast(
                        MotorDatabaseManager, context.get("motor_db_manager")
                    ),
                    security_manager=_cast(
                        SecurityManager, context.get("security_manager")
                    ),
                    request=context.get("request"),
                )
            else:
                ctx = context

            # Check if user has the required role
            if not await ctx.has_role(role):
                raise AuthorizationError(
                    f"Role '{role}' required to access this resource",
                    code="INSUFFICIENT_ROLE",
                )

            # If authorized, proceed with the resolver
            return await resolver_func(*args, **kwargs)

        return cast(CF, wrapper)

    return decorator


def require_any_permission(permissions: list[str]) -> Callable[[CF], CF]:
    """
    Decorator to require any of the specified permissions for a GraphQL resolver.

    Args:
        permissions: List of permissions, user needs at least one

    Example:
        @require_any_permission(["users:read", "users:write"])
        @strawberry.field
        async def users(self, info: Info) -> List[User]:
            return await get_users()
    """

    def decorator(resolver_func: CF) -> CF:
        @functools.wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from kwargs or args
            info = kwargs.get("info") or (args[1] if len(args) > 1 else None)

            if not info or not hasattr(info, "context"):
                raise AuthenticationError("GraphQL context not available")

            context = info.context
            from typing import cast as _cast

            from app.core.motor_database import MotorDatabaseManager
            from app.core.security import SecurityManager
            from app.graphql.context import GraphQLContext

            if isinstance(context, dict):
                ctx = GraphQLContext(
                    motor_db_manager=_cast(
                        MotorDatabaseManager, context.get("motor_db_manager")
                    ),
                    security_manager=_cast(
                        SecurityManager, context.get("security_manager")
                    ),
                    request=context.get("request"),
                )
            else:
                ctx = context

            # Check if user has any of the required permissions
            if not await ctx.has_any_permission(permissions):
                perm_list = ", ".join(permissions)
                raise AuthorizationError(
                    f"One of these permissions required: {perm_list}",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            # If authorized, proceed with the resolver
            return await resolver_func(*args, **kwargs)

        return cast(CF, wrapper)

    return decorator


def require_all_permissions(permissions: list[str]) -> Callable[[CF], CF]:
    """
    Decorator to require all of the specified permissions for a GraphQL resolver.

    Args:
        permissions: List of permissions, user needs all of them

    Example:
        @require_all_permissions(["users:write", "roles:read"])
        @strawberry.mutation
        async def assign_role(self, info: Info, user_id: str, role_id: str) -> bool:
            return await assign_user_role(user_id, role_id)
    """

    def decorator(resolver_func: CF) -> CF:
        @functools.wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from kwargs or args
            info = kwargs.get("info") or (args[1] if len(args) > 1 else None)

            if not info or not hasattr(info, "context"):
                raise AuthenticationError("GraphQL context not available")

            context = info.context
            from typing import cast as _cast

            from app.core.motor_database import MotorDatabaseManager
            from app.core.security import SecurityManager
            from app.graphql.context import GraphQLContext

            if isinstance(context, dict):
                ctx = GraphQLContext(
                    motor_db_manager=_cast(
                        MotorDatabaseManager, context.get("motor_db_manager")
                    ),
                    security_manager=_cast(
                        SecurityManager, context.get("security_manager")
                    ),
                    request=context.get("request"),
                )
            else:
                ctx = context

            # Check if user has all required permissions
            if not await ctx.has_all_permissions(permissions):
                perm_list = ", ".join(permissions)
                raise AuthorizationError(
                    f"All these permissions required: {perm_list}",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            # If authorized, proceed with the resolver
            return await resolver_func(*args, **kwargs)

        return cast(CF, wrapper)

    return decorator


def require_authentication() -> Callable[[CF], CF]:
    """
    Decorator to require authentication (any logged-in user) for a GraphQL resolver.

    Example:
        @require_authentication()
        @strawberry.field
        async def profile(self, info: Info) -> User:
            return info.context.current_user
    """

    def decorator(resolver_func: CF) -> CF:
        @functools.wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from kwargs or args
            info = kwargs.get("info") or (args[1] if len(args) > 1 else None)

            if not info or not hasattr(info, "context"):
                raise AuthenticationError("GraphQL context not available")

            context = info.context
            from typing import cast as _cast

            from app.core.motor_database import MotorDatabaseManager
            from app.core.security import SecurityManager
            from app.graphql.context import GraphQLContext

            if isinstance(context, dict):
                ctx = GraphQLContext(
                    motor_db_manager=_cast(
                        MotorDatabaseManager, context.get("motor_db_manager")
                    ),
                    security_manager=_cast(
                        SecurityManager, context.get("security_manager")
                    ),
                    request=context.get("request"),
                )
            else:
                ctx = context

            # Ensure we evaluate authentication state
            await ctx.get_current_user()
            # Check if user is authenticated
            if not ctx.is_authenticated:
                raise AuthenticationError("Authentication required")

            # If authenticated, proceed with the resolver
            return await resolver_func(*args, **kwargs)

        return cast(CF, wrapper)

    return decorator


# Helper functions for manual authorization checks
async def check_permission(info: Info, permission: str) -> bool:
    """
    Manually check if the current user has a specific permission.

    Args:
        info: GraphQL resolver info object
        permission: Permission to check

    Returns:
        True if user has permission, False otherwise
    """
    if not info or not hasattr(info, "context"):
        return False

    context = info.context
    from typing import cast as _cast

    from app.core.motor_database import MotorDatabaseManager
    from app.core.security import SecurityManager
    from app.graphql.context import GraphQLContext

    if isinstance(context, dict):
        ctx = GraphQLContext(
            motor_db_manager=_cast(
                MotorDatabaseManager, context.get("motor_db_manager")
            ),
            security_manager=_cast(SecurityManager, context.get("security_manager")),
            request=context.get("request"),
        )
    else:
        ctx = context
    return await ctx.has_permission(permission)


async def check_role(info: Info, role: str) -> bool:
    """
    Manually check if the current user has a specific role.

    Args:
        info: GraphQL resolver info object
        role: Role to check

    Returns:
        True if user has role, False otherwise
    """
    if not info or not hasattr(info, "context"):
        return False

    context = info.context
    from typing import cast as _cast

    from app.core.motor_database import MotorDatabaseManager
    from app.core.security import SecurityManager
    from app.graphql.context import GraphQLContext

    if isinstance(context, dict):
        ctx = GraphQLContext(
            motor_db_manager=_cast(
                MotorDatabaseManager, context.get("motor_db_manager")
            ),
            security_manager=_cast(SecurityManager, context.get("security_manager")),
            request=context.get("request"),
        )
    else:
        ctx = context
    return await ctx.has_role(role)


async def get_current_user(info: Info) -> Optional[Any]:
    """
    Get the current user from GraphQL context.

    Args:
        info: GraphQL resolver info object

    Returns:
        Current user object or None if not authenticated
    """
    if not info or not hasattr(info, "context"):
        return None

    context = info.context
    from typing import cast as _cast

    from app.core.motor_database import MotorDatabaseManager
    from app.core.security import SecurityManager
    from app.graphql.context import GraphQLContext

    if isinstance(context, dict):
        ctx = GraphQLContext(
            motor_db_manager=_cast(
                MotorDatabaseManager, context.get("motor_db_manager")
            ),
            security_manager=_cast(SecurityManager, context.get("security_manager")),
            request=context.get("request"),
        )
        return await ctx.get_current_user()

    # Try new GraphQLContext first
    if hasattr(context, "get_current_user"):
        return await context.get_current_user()

    # Fallback to old context structure
    if hasattr(context, "current_user"):
        return context.current_user

    # Ultimate fallback
    return context.get("user")
