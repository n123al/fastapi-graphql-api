"""
Main GraphQL schema definition for the FastAPI GraphQL API.

This module combines all query and mutation resolvers into a unified schema,
providing a single entry point for GraphQL operations while maintaining
modular organization of resolver logic.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import strawberry
from strawberry.types import Info

from app.core.motor_database import motor_db_manager
from app.data.repositories import UserRepository
from app.graphql.mutations.user_mutations import UserMutations
from app.graphql.queries import SystemQueries, UserQueries
from app.graphql.queries.group_queries import GroupQueries
from app.graphql.queries.permission_queries import PermissionQueries
from app.graphql.queries.role_queries import RoleQueries
from app.graphql.types.types import (
    AccessTokenPayload,
    AuthPayload,
    Group,
    LoginInput,
    Permission,
    Role,
    SetPasswordInput,
    User,
    UserInput,
)
from app.services.auth import AuthenticationService


@strawberry.type
class Query:
    """
    Main GraphQL Query type combining all entity-specific queries.

    This class provides a unified interface for all GraphQL query operations
    by delegating to service layer methods for each specific domain
    (users, roles, permissions, groups, system).

    The modular approach allows for easy maintenance and extension of query
    functionality while keeping the schema definition clean and organized.
    """

    @strawberry.field
    async def user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """Get user by ID."""
        return await UserQueries().user(info, id)

    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        """Get current authenticated user."""
        return await UserQueries().me(info)

    @strawberry.field
    async def users(self, info: Info, limit: int = 100) -> List[User]:
        """Get all active users."""
        result: List[User] = await UserQueries().users(info, limit)
        return result

    @strawberry.field
    async def user_by_username(self, info: Info, username: str) -> Optional[User]:
        """Get user by username."""
        result: Optional[User] = await UserQueries().user_by_username(info, username)
        return result

    @strawberry.field
    async def user_by_email(self, info: Info, email: str) -> Optional[User]:
        """Get user by email."""
        result: Optional[User] = await UserQueries().user_by_email(info, email)
        return result

    @strawberry.field
    async def role(self, info: Info, id: strawberry.ID) -> Optional[Role]:
        """Get role by ID."""
        return await RoleQueries().role(info, id)

    @strawberry.field
    async def roles(self, info: Info, limit: int = 100) -> List[Role]:
        """Get all active roles."""
        result: List[Role] = await RoleQueries().roles(info, limit)
        return result

    @strawberry.field
    async def permission(self, info: Info, id: strawberry.ID) -> Optional[Permission]:
        """Get permission by ID."""
        return await PermissionQueries().permission(info, id)

    @strawberry.field
    async def permissions(self, info: Info, limit: int = 100) -> List[Permission]:
        """Get all active permissions."""
        result: List[Permission] = await PermissionQueries().permissions(info, limit)
        return result

    @strawberry.field
    async def group(self, info: Info, id: strawberry.ID) -> Optional[Group]:
        """Get group by ID."""
        return await GroupQueries().group(info, id)

    @strawberry.field
    async def groups(self, info: Info, limit: int = 100) -> List[Group]:
        """Get all active groups."""
        result: List[Group] = await GroupQueries().groups(info, limit)
        return result

    @strawberry.field
    async def system_status(self) -> str:
        """Get system status."""
        return await SystemQueries().system_status()


@strawberry.type
class Mutation:
    """
    Main GraphQL Mutation type combining all entity-specific mutations.

    This class provides a unified interface for all GraphQL mutation operations
    by delegating to service layer methods for each specific domain.
    Currently includes user mutations with room for additional entity mutations.

    The modular approach allows for easy maintenance and extension of mutation
    functionality while keeping the schema definition clean and organized.
    """

    @strawberry.mutation
    async def create_user(self, info: Info, input: UserInput) -> User:
        """Create a new user."""
        result: User = await UserMutations().create_user(info, input)
        return result

    @strawberry.mutation
    async def update_user(
        self, info: Info, id: strawberry.ID, input: UserInput
    ) -> Optional[User]:
        """Update an existing user."""
        result: Optional[User] = await UserMutations().update_user(info, id, input)
        return result

    @strawberry.mutation
    async def set_password(self, info: Info, input: SetPasswordInput) -> bool:
        service = AuthenticationService(UserRepository())
        return await service.set_password_with_token(input.token, input.password)

    @strawberry.mutation
    async def send_onboarding_email(self, info: Info, id: strawberry.ID) -> bool:
        return await UserMutations().send_onboarding_email(info, id)

    @strawberry.mutation
    async def delete_user(self, info: Info, id: strawberry.ID) -> bool:
        """Delete a user."""
        result: bool = await UserMutations().delete_user(info, id)
        return result

    @strawberry.mutation
    async def activate_user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """Activate a user."""
        result: Optional[User] = await UserMutations().activate_user(info, id)
        return result

    @strawberry.mutation
    async def deactivate_user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """Deactivate a user."""
        result: Optional[User] = await UserMutations().deactivate_user(info, id)
        return result

    @strawberry.mutation
    async def login(self, info: Info, input: LoginInput) -> AuthPayload:
        auth_service = AuthenticationService(UserRepository())
        user = await auth_service.authenticate_user(input.identifier, input.password)
        tokens = await auth_service.generate_tokens(user)
        return AuthPayload(
            accessToken=tokens["access_token"],
            refreshToken=tokens["refresh_token"],
            tokenType=tokens["token_type"],
            expiresIn=tokens["expires_in"],
        )

    @strawberry.mutation(name="refreshToken")  # type: ignore[misc]
    async def refresh_token(self, info: Info, refreshToken: str) -> AccessTokenPayload:
        auth_service = AuthenticationService(UserRepository())
        data = await auth_service.refresh_access_token(refreshToken)
        return AccessTokenPayload(
            accessToken=data["access_token"],
            tokenType=data["token_type"],
            expiresIn=data["expires_in"],
        )


async def create_graphql_schema() -> strawberry.Schema:
    """
    Create and configure the main GraphQL schema.

    This function constructs the complete GraphQL schema by combining
    the Query and Mutation types with all their respective resolver methods.

    Returns:
        strawberry.Schema: The complete GraphQL schema ready for use

    Note:
        This schema includes all available queries and mutations for the API,
        providing a unified interface for all GraphQL operations.
    """
    return strawberry.Schema(query=Query, mutation=Mutation)


# Export the schema creation function for use in the main application
__all__ = ["create_graphql_schema"]
