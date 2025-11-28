"""
Base service classes and interfaces for business logic layer.

This module provides abstract base classes and common functionality for
all service implementations, ensuring consistent interfaces and behavior
across the application.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.data import BaseRepository
from app.data.models.base import BaseDataModel

T = TypeVar("T", bound=BaseDataModel)


class BaseService(ABC, Generic[T]):
    """
    Abstract base class for all service implementations.

    This class provides common functionality and defines the interface
    that all service classes must implement.

    Type Parameters:
        T: The data model type that the service manages

    Attributes:
        repository: The data repository for CRUD operations
        service_name: Name of the service for logging and identification

    Example:
        ```python
        class UserService(BaseService[User]):
            def __init__(self, repository: UserRepository):
                super().__init__(repository, "UserService")
        ```
    """

    def __init__(self, repository: BaseRepository[T], service_name: str):
        """
        Initialize the base service.

        Args:
            repository: Data repository for CRUD operations
            service_name: Name of the service for identification
        """
        self.repository: BaseRepository[T] = repository
        self.service_name: str = service_name

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """
        Validate that required fields are present in the data.

        Args:
            data: Dictionary containing data to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required fields are missing
        """
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None or data[field] == ""
        ]

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def _validate_unique_field(
        self, field_name: str, field_value: Any, exclude_id: Optional[str] = None
    ) -> None:
        """
        Validate that a field value is unique across records.

        Args:
            field_name: Name of the field to check
            field_value: Value to check for uniqueness
            exclude_id: ID of record to exclude from check (for updates)

        Raises:
            ConflictError: If the field value is not unique
        """
        # This would need to be implemented by specific services
        # as it depends on the repository implementation
        pass

    async def get_by_id(self, record_id: str) -> T:
        """
        Retrieve a record by its ID.

        Args:
            record_id: Unique identifier of the record

        Returns:
            The record if found, None otherwise

        Raises:
            NotFoundError: If record is not found
        """
        record = await self.repository.get_by_id(record_id)
        if not record:
            raise NotFoundError(f"{self.service_name} not found with ID: {record_id}")
        return record

    async def get_all(self, limit: int = 100, skip: int = 0, **filters: Any) -> List[T]:
        """
        Retrieve multiple records with filtering.

        Args:
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            **filters: Additional filter criteria

        Returns:
            List of records matching the criteria
        """
        return await self.repository.get_all(limit=limit, skip=skip, **filters)

    async def count(self, **filters: Any) -> int:
        """
        Count records matching the filter criteria.

        Args:
            **filters: Filter criteria

        Returns:
            Number of matching records
        """
        return await self.repository.count(**filters)

    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data: Data for the new record

        Returns:
            The created record

        Note:
            This method should be implemented by specific service classes
            to handle business logic validation before creation.
        """
        raise NotImplementedError("Subclasses must implement create method")

    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.

        Args:
            record_id: Unique identifier of the record
            data: Data to update

        Returns:
            The updated record if successful, None otherwise

        Note:
            This method should be implemented by specific service classes
            to handle business logic validation before update.
        """
        raise NotImplementedError("Subclasses must implement update method")

    async def delete(self, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            record_id: Unique identifier of the record

        Returns:
            True if deletion was successful, False otherwise
        """
        # Check if record exists
        await self.get_by_id(record_id)  # This will raise NotFoundError if not found
        return await self.repository.delete(record_id)

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Log service operations for auditing and debugging.

        Args:
            operation: Name of the operation
            details: Additional details about the operation
        """
        # Integrate with the application's logging system here
        return None
