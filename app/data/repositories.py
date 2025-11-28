"""
Repository pattern implementation for data access layer.

This module provides repository classes that bridge the gap between
Pydantic data models and database operations, implementing the
repository pattern for clean data access.
"""

from datetime import datetime, timezone
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from bson import ObjectId

from app.core.exceptions import DatabaseConnectionError, ValidationError
from app.core.motor_database import motor_db_manager
from app.data.models.base import BaseDataModel

if TYPE_CHECKING:
    from .models.group import Group
    from .models.permission import Permission
    from .models.role import Role
    from .models.user import User

T = TypeVar("T", bound=BaseDataModel)


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations.

    This abstract base class defines the interface for all repositories
    and provides common functionality for data access operations.

    Type Parameters:
        T: The data model type (must extend BaseDataModel)

    Attributes:
        model_class: The Pydantic model class for validation
        collection_name: MongoDB collection name

    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            def __init__(self):
                super().__init__(User, "users")
        ```
    """

    def __init__(self, model_class: Type[T], collection_name: str):
        """
        Initialize the repository.

        Args:
            model_class: The Pydantic model class for validation
            collection_name: MongoDB collection name
        """
        self.model_class = model_class
        self.collection_name = collection_name

    @property
    def collection(self) -> Any:
        """Get the MongoDB collection."""
        if not motor_db_manager.is_connected or motor_db_manager.database is None:
            raise DatabaseConnectionError("Database connection not available")
        return motor_db_manager.database[self.collection_name]

    def _prepare_for_storage(self, model: T) -> Dict[str, Any]:
        """
        Prepare model data for database storage.

        Args:
            model: The Pydantic model instance

        Returns:
            Dictionary ready for MongoDB storage
        """
        # Don't exclude sensitive fields when storing to database
        data = model.to_dict(exclude_sensitive=False)

        # Convert string ID to ObjectId if present
        if "id" in data and data["id"]:
            data["_id"] = ObjectId(data["id"])
            del data["id"]

        return data

    def _prepare_from_storage(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare database document for model creation.

        Args:
            doc: The MongoDB document

        Returns:
            Dictionary ready for Pydantic model creation
        """
        # Convert ObjectId to string ID
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for key in ("role_ids", "group_ids", "permission_ids"):
            if key in doc and isinstance(doc[key], list):
                doc[key] = [str(v) if isinstance(v, ObjectId) else v for v in doc[key]]

        return doc

    async def create(self, model: T) -> T:
        """
        Create a new record in the database.

        Args:
            model: The Pydantic model instance to create

        Returns:
            The created model with generated fields

        Raises:
            ValidationError: If model validation fails
            DatabaseConnectionError: If database operation fails
        """
        try:
            # Validate the model (Pydantic v2 compatible)
            if hasattr(model, "model_validate"):
                model.model_validate(model)
            elif hasattr(model, "validate"):
                model.validate(model)

            # Prepare data for storage
            data = self._prepare_for_storage(model)

            # Set timestamps
            now = datetime.now(timezone.utc)
            data.setdefault("created_at", now)
            data.setdefault("updated_at", now)

            # Insert into database
            result = await self.collection.insert_one(data)

            # Update model with generated ID
            model.id = str(result.inserted_id)

            return model

        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to create {self.collection_name}: {str(e)}"
            )

    async def get_by_id(self, record_id: str) -> Optional[T]:
        """
        Retrieve a record by its ID.

        Args:
            record_id: The record's unique identifier

        Returns:
            The model instance if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(record_id)})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve {self.collection_name}: {str(e)}"
            )

    async def update(self, record_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.

        Args:
            record_id: The record's unique identifier
            update_data: Dictionary containing fields to update

        Returns:
            The updated model instance if successful, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        # Set updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(record_id)}, {"$set": update_data}
            )

            if result.modified_count > 0:
                return await self.get_by_id(record_id)
            return None
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to update {self.collection_name}: {str(e)}"
            )

    async def delete(self, record_id: str) -> bool:
        """
        Delete a record (soft delete by default).

        Args:
            record_id: The record's unique identifier

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(record_id)},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.now(timezone.utc),
                        "is_active": False,
                    }
                },
            )
            return bool(getattr(result, "modified_count", 0) > 0)
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to delete {self.collection_name}: {str(e)}"
            )

    async def get_all(self, limit: int = 100, skip: int = 0, **filters: Any) -> List[T]:
        """
        Retrieve multiple records with filtering.

        Args:
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            **filters: Additional filter criteria

        Returns:
            List of model instances

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            # Default filters for active, non-deleted records
            # Note: is_deleted might not exist in older records, treat null/missing as False
            query = {"is_active": True, "is_deleted": {"$ne": True}}
            query.update(filters)

            cursor = self.collection.find(query).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)

            records = []
            for doc in docs:
                prepared_data = self._prepare_from_storage(doc)
                records.append(self.model_class(**prepared_data))

            return records
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve {self.collection_name}: {str(e)}"
            )

    async def count(self, **filters: Any) -> int:
        """
        Count records matching the filter criteria.

        Args:
            **filters: Filter criteria

        Returns:
            Number of matching records

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            query = {"is_active": True, "is_deleted": {"$ne": True}}
            query.update(filters)
            return cast(int, await self.collection.count_documents(query))
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to count {self.collection_name}: {str(e)}"
            )


class UserRepository(BaseRepository["User"]):
    """Repository for User data operations."""

    def __init__(self) -> None:
        from .models.user import User

        super().__init__(User, "users")

    async def get_by_username(self, username: str) -> Optional["User"]:
        """
        Retrieve a user by username.

        Args:
            username: The user's username

        Returns:
            User instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one({"username": username})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve user by username: {str(e)}"
            )

    async def get_by_email(self, email: str) -> Optional["User"]:
        """
        Retrieve a user by email address.

        Args:
            email: The user's email address

        Returns:
            User instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one({"email": email})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve user by email: {str(e)}")

    async def get_by_email_or_username(self, identifier: str) -> Optional["User"]:
        """
        Retrieve a user by email address or username.

        Args:
            identifier: The user's email address or username

        Returns:
            User instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one(
                {"$or": [{"email": identifier}, {"username": identifier}]}
            )
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve user by email or username: {str(e)}"
            )


class RoleRepository(BaseRepository["Role"]):
    """Repository for Role data operations."""

    def __init__(self) -> None:
        from .models.role import Role

        super().__init__(Role, "roles")

    async def get_by_name(self, name: str) -> Optional["Role"]:
        """
        Retrieve a role by name.

        Args:
            name: The role's name

        Returns:
            Role instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one({"name": name})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve role by name: {str(e)}")

    async def get_system_roles(self, limit: int = 100) -> List["Role"]:
        """
        Retrieve all system roles.

        Args:
            limit: Maximum number of roles to return

        Returns:
            List of system roles
        """
        try:
            cursor = self.collection.find({"is_system_role": True}).limit(limit)
            docs = await cursor.to_list(length=limit)

            roles = []
            for doc in docs:
                prepared_data = self._prepare_from_storage(doc)
                roles.append(self.model_class(**prepared_data))

            return roles
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve system roles: {str(e)}")


class PermissionRepository(BaseRepository["Permission"]):
    """Repository for Permission data operations."""

    def __init__(self) -> None:
        from .models.permission import Permission

        super().__init__(Permission, "permissions")

    async def get_by_resource_action(
        self, resource: str, action: str
    ) -> Optional["Permission"]:
        """
        Retrieve a permission by resource and action.

        Args:
            resource: The resource name
            action: The action name

        Returns:
            Permission instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one(
                {"resource": resource, "action": action}
            )
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve permission: {str(e)}")

    async def get_by_name(self, name: str) -> Optional["Permission"]:
        try:
            doc = await self.collection.find_one({"name": name})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve permission by name: {str(e)}"
            )


class GroupRepository(BaseRepository["Group"]):
    """Repository for Group data operations."""

    def __init__(self) -> None:
        from .models.group import Group

        super().__init__(Group, "groups")

    async def get_by_name(self, name: str) -> Optional["Group"]:
        """
        Retrieve a group by name.

        Args:
            name: The group's name

        Returns:
            Group instance if found, None otherwise
        """
        try:
            doc = await self.collection.find_one({"name": name})
            if doc:
                prepared_data = self._prepare_from_storage(doc)
                return self.model_class(**prepared_data)
            return None
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve group by name: {str(e)}")

    async def get_by_member(self, user_id: str, limit: int = 100) -> List["Group"]:
        """
        Retrieve all groups that a user is a member of.

        Args:
            user_id: The user's ID
            limit: Maximum number of groups to return

        Returns:
            List of groups the user belongs to
        """
        try:
            cursor = self.collection.find({"member_ids": user_id}).limit(limit)
            docs = await cursor.to_list(length=limit)

            groups = []
            for doc in docs:
                prepared_data = self._prepare_from_storage(doc)
                groups.append(self.model_class(**prepared_data))

            return groups
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to retrieve groups by member: {str(e)}"
            )

    async def get_public_groups(self, limit: int = 100) -> List["Group"]:
        """
        Retrieve all public groups.

        Args:
            limit: Maximum number of groups to return

        Returns:
            List of public groups
        """
        try:
            cursor = self.collection.find({"is_public": True}).limit(limit)
            docs = await cursor.to_list(length=limit)

            groups = []
            for doc in docs:
                prepared_data = self._prepare_from_storage(doc)
                groups.append(self.model_class(**prepared_data))

            return groups
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to retrieve public groups: {str(e)}")
