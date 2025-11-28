"""
GraphQL query resolvers for Permission entities.

This module contains all GraphQL query operations related to permission management,
including fetching individual permissions, permission lists, and permission-specific data.
"""

from typing import List, Optional

import strawberry
from bson import ObjectId
from strawberry.types import Info

from app.core.motor_database import motor_db_manager
from app.graphql.auth import (
    require_any_permission,
    require_authentication,
    require_permission,
)
from app.graphql.types.types import Permission


class PermissionQueries:
    """
    GraphQL query resolvers for permission-related operations.

    This class contains all query methods for retrieving permission data,
    including individual permissions, permission lists, and permission-specific information.
    """

    @require_permission("permissions:read")
    async def permission(self, info: Info, id: strawberry.ID) -> Optional[Permission]:
        """
        Retrieve a single permission by their unique identifier.
        Requires permissions:read permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the permission to retrieve

        Returns:
            Permission object if found, None otherwise

        Raises:
            AuthorizationError if user lacks permissions:read permission
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None

            collection = motor_db_manager.database["permissions"]
            doc = await collection.find_one({"_id": ObjectId(id), "is_active": True})

            if doc:
                doc["id"] = str(doc.pop("_id"))
                return Permission(**doc)

            return None
        except Exception:
            return None

    @require_permission("permissions:read")
    async def permissions(self, info: Info, limit: int = 100) -> List[Permission]:
        """
        Retrieve a list of all active permissions.
        Requires permissions:read permission.

        Args:
            info: GraphQL context info
            limit: Maximum number of permissions to return (default: 100)

        Returns:
            List of Permission objects, empty list if no permissions found or connection issues

        Raises:
            AuthorizationError if user lacks permissions:read permission

        Note:
            Only returns active permissions (is_active: true) and respects the limit parameter
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []

            collection = motor_db_manager.database["permissions"]
            docs = (
                await collection.find({"is_active": True}).limit(limit).to_list(limit)
            )

            permissions = []
            for doc in docs:
                doc["id"] = str(doc.pop("_id"))
                permissions.append(Permission(**doc))

            return permissions
        except Exception:
            return []

    @require_permission("permissions:read")
    async def permission_by_name(self, info: Info, name: str) -> Optional[Permission]:
        """
        Retrieve a permission by its name.
        Requires permissions:read permission.

        Args:
            info: GraphQL context info
            name: The name of the permission to search for

        Returns:
            Permission object if found, None otherwise

        Raises:
            AuthorizationError if user lacks permissions:read permission
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None

            collection = motor_db_manager.database["permissions"]
            doc = await collection.find_one({"name": name, "is_active": True})

            if doc:
                doc["id"] = str(doc.pop("_id"))
                return Permission(**doc)

            return None
        except Exception:
            return None

    @require_permission("permissions:read")
    async def permissions_by_resource(
        self, info: Info, resource: str
    ) -> List[Permission]:
        """
        Retrieve all permissions for a specific resource.
        Requires permissions:read permission.

        Args:
            info: GraphQL context info
            resource: The resource name to filter permissions by

        Returns:
            List of Permission objects for the specified resource

        Raises:
            AuthorizationError if user lacks permissions:read permission
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []

            collection = motor_db_manager.database["permissions"]
            docs = await collection.find(
                {"resource": resource, "is_active": True}
            ).to_list(None)

            permissions = []
            for doc in docs:
                doc["id"] = str(doc.pop("_id"))
                permissions.append(Permission(**doc))

            return permissions
        except Exception:
            return []
