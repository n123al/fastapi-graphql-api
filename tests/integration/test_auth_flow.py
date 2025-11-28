import pytest
import asyncio
from app.core.motor_database import motor_db_manager
from app.core.auth_strategies import AuthenticationContext, UsernamePasswordAuthStrategy, AuthorizationService
from app.data.repositories import UserRepository, RoleRepository, PermissionRepository
from app.data.models.user import User
from app.data.models.role import Role
from app.data.models.permission import Permission
from app.graphql.context import GraphQLContext
from app.core.security import security_manager
from unittest.mock import MagicMock

@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_flow_integration(setup_test_database) -> None:
    """
    Test the complete login and permission check flow.
    This simulates what happens when you login and make a GraphQL query.
    
    Note: This test requires a MongoDB connection. Skip if not available.
    """
    # Setup: Create admin user
    user_repo = UserRepository()
    role_repo = RoleRepository()
    perm_repo = PermissionRepository()
    
    # Create permissions
    perm = Permission(
        name="users:read",
        description="Read users",
        resource="users",
        action="read"
    )
    perm = await perm_repo.create(perm)
    
    # Create role
    role = Role(
        name="admin",
        description="Admin role",
        permission_ids=[str(perm.id)]
    )
    role = await role_repo.create(role)
    
    # Create admin user
    from app.core.security import get_password_hash
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        role_ids=[str(role.id)],
        is_superuser=True
    )
    user = await user_repo.create(user)
    
    # Step 1: Authenticate
    auth_context = AuthenticationContext(UsernamePasswordAuthStrategy())
    credentials = {
        "email": "admin@example.com",
        "password": "password123"
    }
    
    authenticated_user = await auth_context.authenticate(credentials)
    assert authenticated_user.id == user.id
    assert authenticated_user.email == "admin@example.com"
    
    # Step 2: Create token
    token_manager = auth_context.strategy.token_manager
    token = token_manager.create_access_token({"sub": str(authenticated_user.id)})
    assert token is not None
    
    # Step 3: Decode token
    decoded = token_manager.decode_token(token)
    assert decoded["sub"] == str(authenticated_user.id)
    
    # Step 4: Load user from database using token
    validated_user = await auth_context.validate_token(token)
    assert validated_user.id == user.id
    
    # Step 5: Check permission
    authz_service = AuthorizationService()
    has_perm = await authz_service.has_permission(validated_user, "users:read")
    assert has_perm is True

@pytest.mark.asyncio
@pytest.mark.integration
async def test_gql_context_integration(setup_test_database):
    """
    Test permission checking through GraphQL context.
    
    Note: This test requires a MongoDB connection. Skip if not available.
    """
    # Setup: Create user and permissions (reusing logic or relying on clean DB)
    # Since DB is dropped per session, we might need to recreate or use fixtures.
    # For simplicity, let's recreate.
    
    user_repo = UserRepository()
    perm_repo = PermissionRepository()
    role_repo = RoleRepository()

    # Create permissions
    perm_read = Permission(
        name="users:read",
        description="Read users",
        resource="users",
        action="read"
    )
    perm_read = await perm_repo.create(perm_read)
    
    # Create role
    role = Role(
        name="viewer",
        description="Viewer role",
        permission_ids=[str(perm_read.id)]
    )
    role = await role_repo.create(role)

    # Create user
    from app.core.security import get_password_hash
    user = User(
        username="viewer",
        email="viewer@example.com",
        hashed_password=get_password_hash("password123"),
        role_ids=[str(role.id)],
        is_superuser=False
    )
    user = await user_repo.create(user)
    
    # Authenticate
    auth_context = AuthenticationContext(UsernamePasswordAuthStrategy())
    token_manager = auth_context.strategy.token_manager
    token = token_manager.create_access_token({"sub": str(user.id)})
    
    # Mock Request
    mock_request = MagicMock()
    mock_request.headers.get.return_value = f"Bearer {token}"
    
    # Create GraphQL context
    gql_context = GraphQLContext(
        motor_db_manager=motor_db_manager,
        security_manager=security_manager,
        request=mock_request
    )
    
    # Test context user
    context_user = await gql_context.get_current_user()
    assert context_user.id == user.id
    
    # Test permissions
    has_read = await gql_context.has_permission("users:read")
    assert has_read is True
    
    has_write = await gql_context.has_permission("users:write")
    assert has_write is False
