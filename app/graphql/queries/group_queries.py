"""
GraphQL query resolvers for Group entities.

This module contains all GraphQL query operations related to group management,
including fetching individual groups, group lists, and group-specific data.
"""

from typing import List, Optional

import strawberry
from bson import ObjectId
from strawberry.types import Info

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.motor_database import motor_db_manager
from app.graphql.auth import (
    check_permission,
    get_current_user,
    require_any_permission,
    require_permission,
)
from app.graphql.types.types import Group


class GroupQueries:
    """
    GraphQL query resolvers for group-related operations.

    This class contains all query methods for retrieving group data,
    including individual groups, group lists, and group-specific information.
    """

    async def group(self, info: Info, id: strawberry.ID) -> Optional[Group]:
        """
        Retrieve a single group by their unique identifier.
        Users can access groups they are members of.
        Accessing other groups requires groups:read permission.

        Args:
            info: GraphQL context info
            id: The unique identifier of the group to retrieve

        Returns:
            Group object if found and authorized, None otherwise

        Raises:
            AuthorizationError if user lacks permission to access this group
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                raise AuthenticationError("Authentication required")

            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None

            collection = motor_db_manager.database["groups"]
            doc = await collection.find_one({"_id": ObjectId(id), "is_active": True})

            if not doc:
                return None

            # Check if user is member of this group
            group_name = doc.get("name")
            if current_user.is_member_of(group_name):
                doc["id"] = str(doc.pop("_id"))
                return Group(**doc)

            # If not a member, check if user has permission to read all groups
            if not await check_permission(info, "groups:read"):
                raise AuthorizationError(
                    "Permission 'groups:read' required to access groups you're not a member of",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            doc["id"] = str(doc.pop("_id"))
            return Group(**doc)

        except (AuthenticationError, AuthorizationError):
            raise
        except Exception:
            return None

    async def groups(self, info: Info, limit: int = 100) -> List[Group]:
        """
        Retrieve a list of all active groups.
        Users can see groups they are members of.
        Seeing all groups requires groups:read permission.

        Args:
            info: GraphQL context info
            limit: Maximum number of groups to return (default: 100)

        Returns:
            List of Group objects, filtered by authorization

        Raises:
            AuthorizationError if user lacks permission

        Note:
            Returns member groups for regular users, all groups for users with groups:read permission
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                raise AuthenticationError("Authentication required")

            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []

            collection = motor_db_manager.database["groups"]

            # If user has groups:read permission, return all groups
            if await check_permission(info, "groups:read"):
                docs = (
                    await collection.find({"is_active": True})
                    .limit(limit)
                    .to_list(limit)
                )
            else:
                # Return only groups user is member of
                user_group_ids = current_user.group_ids
                if not user_group_ids:
                    return []

                docs = (
                    await collection.find(
                        {
                            "_id": {"$in": [ObjectId(gid) for gid in user_group_ids]},
                            "is_active": True,
                        }
                    )
                    .limit(limit)
                    .to_list(limit)
                )

            groups = []
            for doc in docs:
                doc["id"] = str(doc.pop("_id"))
                groups.append(Group(**doc))

            return groups
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception:
            return []

    async def group_by_name(self, info: Info, name: str) -> Optional[Group]:
        """
        Retrieve a group by its name.
        Users can access groups they are members of.
        Accessing other groups requires groups:read permission.

        Args:
            info: GraphQL context info
            name: The name of the group to search for

        Returns:
            Group object if found and authorized, None otherwise

        Raises:
            AuthorizationError if user lacks permission to access this group
        """
        try:
            # Get current user from context
            current_user = await get_current_user(info)
            if not current_user:
                raise AuthenticationError("Authentication required")

            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return None

            collection = motor_db_manager.database["groups"]
            doc = await collection.find_one({"name": name, "is_active": True})

            if not doc:
                return None

            # Check if user is member of this group
            if current_user.is_member_of(name):
                doc["id"] = str(doc.pop("_id"))
                return Group(**doc)

            # If not a member, check if user has permission to read all groups
            if not await check_permission(info, "groups:read"):
                raise AuthorizationError(
                    "Permission 'groups:read' required to access groups you're not a member of",
                    code="INSUFFICIENT_PERMISSIONS",
                )

            doc["id"] = str(doc.pop("_id"))
            return Group(**doc)

        except (AuthenticationError, AuthorizationError):
            raise
        except Exception:
            return None

    @require_permission("groups:read")
    async def system_groups(self, info: Info) -> List[Group]:
        """
        Retrieve all system groups.
        Requires groups:read permission.

        Args:
            info: GraphQL context info

        Returns:
            List of system Group objects, empty list if none found or connection issues

        Raises:
            AuthorizationError if user lacks groups:read permission

        Note:
            System groups are marked with is_system_group: true and cannot be deleted
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return []

            collection = motor_db_manager.database["groups"]
            docs = await collection.find(
                {"is_system_group": True, "is_active": True}
            ).to_list(None)

            groups = []
            for doc in docs:
                doc["id"] = str(doc.pop("_id"))
                groups.append(Group(**doc))

            return groups
        except Exception:
            return []
