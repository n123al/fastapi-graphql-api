# Authentication and Authorization System Documentation

## Overview

This document describes the authentication and authorization system implemented in the FastAPI GraphQL API. The system uses JWT (JSON Web Tokens) for authentication and implements role-based access control (RBAC) with fine-grained permissions.

## Architecture

### Authentication Flow

1. **User Registration/Login**: Users authenticate using username/password or email/password
2. **Token Generation**: Upon successful authentication, JWT access and refresh tokens are generated
3. **Token Validation**: Each request includes the JWT token in the Authorization header
4. **User Context**: The GraphQL context validates the token and provides user information

### Authorization Flow

1. **Permission-Based**: Each GraphQL resolver can require specific permissions
2. **Role-Based**: Users can be assigned roles that grant them permissions
3. **Context-Aware**: Authorization checks consider the current user and their permissions
4. **Smart Access**: Users can access their own data without special permissions

## Components

### 1. Security Manager (`app.core.security`)

The `SecurityManager` class provides the main interface for authentication and authorization:

```python
from app.core.security import security_manager

# Get current user from JWT token
current_user = await security_manager.get_current_user(credentials)

# Check permissions
has_permission = security_manager.has_permission(user, "users:read")

# Create access token
token = security_manager.create_access_token({"sub": user.id})
```

**Key Functions:**
- `get_current_user()`: Extract user from JWT token
- `get_current_active_user()`: Get current user and ensure they're active
- `require_permission()`: Dependency for specific permissions
- `require_role()`: Dependency for specific roles
- `require_any_permission()`: Dependency for any of multiple permissions
- `require_all_permissions()`: Dependency for all specified permissions

### 2. Authentication Strategies (`app.core.auth_strategies`)

Multiple authentication strategies are supported:

- **UsernamePasswordAuthStrategy**: Traditional username/password authentication
- **EmailAuthStrategy**: Email/password authentication
- **JWTAuthenticationStrategy**: JWT token validation
- **AnonymousAuthenticationStrategy**: Anonymous/guest access

**Token Management:**
- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Tokens are signed with HS256 algorithm
- Secret key is configurable via environment variables

### 3. GraphQL Context (`app.graphql.context`)

The GraphQL context provides authentication and authorization capabilities:

```python
from app.graphql.context import GraphQLContext

context = GraphQLContext(
    motor_db_manager=motor_db_manager,
    security_manager=security_manager,
    request=request
)

# Get current user
user = await context.get_current_user()

# Check permissions
has_perm = context.has_permission("users:write")
has_role = context.has_role("admin")
```

**Context Methods:**
- `get_current_user()`: Get the authenticated user
- `has_permission(permission)`: Check if user has specific permission
- `has_role(role)`: Check if user has specific role
- `has_any_permission(permissions)`: Check if user has any of the permissions
- `has_all_permissions(permissions)`: Check if user has all permissions
- `is_authenticated`: Property indicating if user is authenticated

### 4. Authorization Decorators (`app.graphql.auth`)

GraphQL-specific authorization decorators for resolvers:

```python
from app.graphql.auth import require_permission, require_role, require_authentication

@require_permission("users:read")
@strawberry.field
async def users(self, info: Info) -> List[User]:
    return await get_users()

@require_role("admin")
@strawberry.field
async def system_stats(self, info: Info) -> SystemStats:
    return await get_system_stats()

@require_authentication()
@strawberry.field
async def profile(self, info: Info) -> User:
    return info.context.current_user
```

**Available Decorators:**
- `@require_permission(permission)`: Require specific permission
- `@require_role(role)`: Require specific role
- `@require_any_permission(permissions)`: Require any of the permissions
- `@require_all_permissions(permissions)`: Require all permissions
- `@require_authentication()`: Require any authenticated user

## Permission System

### Permission Format

Permissions follow the format: `resource:action`

**Examples:**
- `users:read` - Read user data
- `users:write` - Create/update user data
- `users:delete` - Delete user data
- `roles:manage` - Manage roles
- `permissions:assign` - Assign permissions to roles

### Built-in Permissions

The system includes these default permissions:

```python
PERMISSIONS = {
    # User permissions
    "users:read": "Read user information",
    "users:write": "Create and update users",
    "users:delete": "Delete users",
    
    # Role permissions
    "roles:read": "Read role information",
    "roles:write": "Create and update roles",
    "roles:delete": "Delete roles",
    "roles:assign": "Assign roles to users",
    
    # Permission permissions
    "permissions:read": "Read permission information",
    "permissions:write": "Create and update permissions",
    "permissions:delete": "Delete permissions",
    "permissions:assign": "Assign permissions to roles",
    
    # Group permissions
    "groups:read": "Read group information",
    "groups:write": "Create and update groups",
    "groups:delete": "Delete groups",
    "groups:manage": "Manage group membership",
    
    # System permissions
    "system:read": "Read system information",
    "system:admin": "Full system administration"
}
```

## Role System

### Default Roles

The system includes these default roles:

1. **Super Admin**: Full system access
   - All permissions
   - System administration capabilities

2. **Admin**: Administrative access
   - User management
   - Role and permission management
   - System monitoring

3. **Moderator**: Content moderation
   - User management (read/write)
   - Limited administrative functions

4. **User**: Standard user access
   - Own profile management
   - Basic read access to public data

5. **Guest**: Limited access
   - Read-only access to public data
   - No modification capabilities

### Role Hierarchy

Roles can inherit permissions from other roles, creating a hierarchy:

```python
DEFAULT_ROLES = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Full system access",
        "permissions": ["*"],  # All permissions
        "inherits_from": []
    },
    "admin": {
        "name": "Admin", 
        "description": "Administrative access",
        "permissions": [
            "users:*",
            "roles:*", 
            "permissions:*",
            "groups:*",
            "system:read"
        ],
        "inherits_from": ["moderator"]
    }
}
```

## Usage Examples

### 1. Basic Authentication

```python
from app.core.security import security_manager

# In your login endpoint
async def login(credentials: LoginCredentials):
    # Authenticate user
    user = await authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

### 2. Protected GraphQL Resolver

```python
import strawberry
from app.graphql.auth import require_permission
from app.graphql.types.types import User

@strawberry.type
class UserQueries:
    @require_permission("users:read")
    @strawberry.field
    async def users(self, info: strawberry.Info) -> List[User]:
        """Get all users (requires users:read permission)."""
        user_service = UserService()
        users = await user_service.get_all_users()
        return [User.from_model(user) for user in users]
    
    @require_authentication()
    @strawberry.field
    async def me(self, info: strawberry.Info) -> User:
        """Get current user (requires authentication)."""
        current_user = await info.context.get_current_user()
        return User.from_model(current_user)
```

### 3. Smart Authorization (Users can access their own data)

```python
@strawberry.type
class UserQueries:
    @strawberry.field
    async def user(self, info: strawberry.Info, id: strawberry.ID) -> Optional[User]:
        """Get user by ID with smart authorization."""
        current_user = await info.context.get_current_user()
        
        # Users can always access their own data
        if current_user and str(current_user.id) == str(id):
            return User.from_model(current_user)
        
        # For other users, check permission
        if not info.context.has_permission("users:read"):
            raise AuthorizationError("Permission 'users:read' required")
        
        user_service = UserService()
        user = await user_service.get_user_by_id(str(id))
        return User.from_model(user) if user else None
```

### 4. Role-Based Access Control

```python
@strawberry.type
class AdminQueries:
    @require_role("admin")
    @strawberry.field
    async def system_stats(self, info: strawberry.Info) -> SystemStats:
        """Get system statistics (requires admin role)."""
        return await get_system_statistics()
    
    @require_any_permission(["users:write", "roles:manage"])
    @strawberry.mutation
    async def assign_role(self, info: strawberry.Info, user_id: str, role_id: str) -> bool:
        """Assign role to user (requires either users:write or roles:manage)."""
        role_service = RoleService()
        return await role_service.assign_role_to_user(user_id, role_id)
```

## Environment Configuration

### Required Environment Variables

```bash
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Authentication
REQUIRE_AUTHENTICATION=true

# Database (for user/role/permission storage)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_graphql_db
```

### Optional Configuration

```bash
# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# File upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads

# Logging
LOG_LEVEL=INFO
```

## Security Best Practices

### 1. Token Security
- Use strong secret keys (minimum 32 characters)
- Rotate secret keys regularly
- Store tokens securely (HTTPS only)
- Implement token refresh mechanism
- Set appropriate token expiration times

### 2. Permission Design
- Follow principle of least privilege
- Use specific permissions (avoid wildcards when possible)
- Regular permission audits
- Document permission requirements

### 3. Authorization Checks
- Always validate permissions server-side
- Don't trust client-side authorization
- Implement defense in depth
- Log authorization failures

### 4. User Management
- Strong password requirements
- Account lockout after failed attempts
- Regular password rotation policies
- Multi-factor authentication support

## Testing

### Unit Tests

```python
import pytest
from app.core.security import security_manager
from app.graphql.auth import require_permission

@pytest.mark.asyncio
async def test_permission_check():
    user = User(permissions=["users:read"])
    has_perm = security_manager.has_permission(user, "users:read")
    assert has_perm is True

@pytest.mark.asyncio
async def test_unauthorized_access():
    with pytest.raises(AuthorizationError):
        # Test unauthorized access
        pass
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_graphql_authorization():
    # Test GraphQL resolver with authorization
    query = """
    query {
        users {
            id
            username
        }
    }
    """
    
    # Test without authentication
    response = await graphql_client.execute(query)
    assert "Authorization error" in response["errors"][0]["message"]
    
    # Test with proper authentication
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = await graphql_client.execute(query, headers=headers)
    assert "data" in response
```

## Troubleshooting

### Common Issues

1. **"Cannot import name 'get_password_hash'"**
   - Ensure all security functions are properly exported in `app.core.__init__.py`
   - Check that `app.core.security` has the required functions

2. **"Permission denied for table"**
   - Check database permissions for the authenticated user
   - Ensure proper role assignments

3. **"Invalid token"**
   - Verify token format and expiration
   - Check secret key configuration
   - Ensure proper token signing algorithm

4. **"GraphQL context not available"**
   - Ensure GraphQL context is properly initialized
   - Check that authorization decorators are used correctly

### Debug Mode

Enable debug mode to get detailed authorization logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
DEBUG=true
```

## Migration Guide

### From Basic Authentication

1. Update imports from `app.core.auth` to `app.core.security`
2. Replace direct password functions with security manager
3. Update token creation to use new functions
4. Add authorization decorators to GraphQL resolvers

### From Role-Only System

1. Add permission definitions to your roles
2. Update authorization checks to use permissions
3. Maintain backward compatibility with role checks
4. Gradually migrate to permission-based system

This authentication and authorization system provides a robust, scalable foundation for securing your GraphQL API while maintaining flexibility for complex authorization requirements.