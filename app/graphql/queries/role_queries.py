"""
GraphQL query resolvers for Role entities.

This module contains all GraphQL query operations related to role management,
including fetching individual roles, role lists, and role-specific data.
"""

import strawberry
from strawberry.types import Info
from typing import List, Optional

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.graphql.types.types import Role
from app.graphql.auth import require_permission, require_any_permission
from app.core.motor_database import motor_db_manager


class RoleQueries:
    """
    GraphQL query resolvers for role-related operations.
    
    This class contains all query methods for retrieving role data,
    including individual roles, role lists, and role-specific information.
    """
    
    @require_any_permission(["roles:read", "users:read"])
    async def role(self, info: Info, id: strawberry.ID) -> Optional[Role]:
        """
        Retrieve a single role by their unique identifier.
        Requires roles:read or users:read permission.
        
        Args:
            info: GraphQL context info
            id: The unique identifier of the role to retrieve
            
        Returns:
            Role object if found, None otherwise
            
        Raises:
            AuthorizationError if user lacks required permission
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None

            collection = motor_db_manager.database["roles"]
            from bson import ObjectId
            doc = await collection.find_one({"_id": ObjectId(str(id)), "is_active": True})
            if doc:
                role_id = str(doc.get("_id")) if doc.get("_id") is not None else str(id)
                return Role(
                    id=strawberry.ID(role_id),
                    name=doc.get("name"),
                    description=doc.get("description"),
                    is_system_role=doc.get("is_system_role", False),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
            return None
        except Exception as e:
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise
            return None
    
    @require_any_permission(["roles:read", "users:read"])
    async def roles(self, info: Info, limit: int = 100) -> List[Role]:
        """
        Retrieve a list of all active roles.
        Requires roles:read or users:read permission.
        
        Args:
            info: GraphQL context info
            limit: Maximum number of roles to return (default: 100)
            
        Returns:
            List of Role objects, empty list if no roles found or service errors
            
        Raises:
            AuthorizationError if user lacks required permission
            
        Note:
            Only returns active roles (is_active: true) and respects the limit parameter
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []

            collection = motor_db_manager.database["roles"]
            docs = await collection.find({"is_active": True}).limit(limit).to_list(limit)

            roles: List[Role] = []
            for doc in docs:
                roles.append(Role(
                    id=strawberry.ID(str(doc.get("_id"))),
                    name=doc.get("name"),
                    description=doc.get("description"),
                    is_system_role=doc.get("is_system_role", False),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                ))
            return roles
        except Exception as e:
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise
            return []
    
    @require_any_permission(["roles:read", "users:read"])
    async def role_by_name(self, info: Info, name: str) -> Optional[Role]:
        """
        Retrieve a role by its name.
        Requires roles:read or users:read permission.
        
        Args:
            info: GraphQL context info
            name: The name of the role to search for
            
        Returns:
            Role object if found, None otherwise
            
        Raises:
            AuthorizationError if user lacks required permission
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None
            
            collection = motor_db_manager.database["roles"]
            doc = await collection.find_one({"name": name, "is_active": True})
            
            if doc:
                return Role(
                    id=strawberry.ID(str(doc.get("_id"))),
                    name=doc.get("name"),
                    description=doc.get("description"),
                    is_system_role=doc.get("is_system_role", False),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
            
            return None
        except Exception:
            return None
    
    @require_permission("roles:read")
    async def system_roles(self, info: Info) -> List[Role]:
        """
        Retrieve all system roles.
        Requires roles:read permission.
        
        Args:
            info: GraphQL context info
            
        Returns:
            List of system Role objects, empty list if none found or connection issues
            
        Raises:
            AuthorizationError if user lacks roles:read permission
            
        Note:
            System roles are marked with is_system_role: true and cannot be deleted
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []
            
            collection = motor_db_manager.database["roles"]
            docs = await collection.find({"is_system_role": True, "is_active": True}).to_list(None)
            
            roles: List[Role] = []
            for doc in docs:
                roles.append(Role(
                    id=strawberry.ID(str(doc.get("_id"))),
                    name=doc.get("name"),
                    description=doc.get("description"),
                    is_system_role=doc.get("is_system_role", False),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                ))
            
            return roles
        except Exception:
            return []