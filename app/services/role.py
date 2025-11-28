"""
Role service for managing role-related operations.

This service provides business logic for role management, including
role creation, updates, and permission assignments.
"""

from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.data.models.role import Role
from app.data.repositories import RoleRepository


class RoleService:
    """
    Service class for role management operations.

    This service encapsulates all business logic related to roles,
    providing a clean interface for role operations while handling
    validation, permissions, and business rules.
    """

    def __init__(self) -> None:
        """Initialize the role service with required repositories."""
        self.role_repository: RoleRepository = RoleRepository()

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """
        Retrieve a role by its ID.

        Args:
            role_id: The role ID as a string

        Returns:
            The role object if found, None otherwise

        Raises:
            NotFoundError: If role is not found
        """
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")

        return role

    async def get_all_roles(self, limit: int = 100) -> List[Role]:
        """
        Retrieve all roles.

        Returns:
            List of all role objects
        """
        return await self.role_repository.get_all(limit=limit)

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieve a role by its name.

        Args:
            name: The role name

        Returns:
            The role object if found, None otherwise
        """
        return await self.role_repository.get_by_name(name)

    async def create_role(self, role_data: Dict[str, Any]) -> Role:
        """
        Create a new role.

        Args:
            role_data: Dictionary containing role data

        Returns:
            The created role object

        Raises:
            ValidationError: If role data is invalid
        """
        # Validate required fields
        if not role_data.get("name"):
            raise ValidationError("Role name is required")

        if not role_data.get("description"):
            raise ValidationError("Role description is required")

        # Check if role with same name already exists
        existing_role = await self.get_role_by_name(role_data["name"])
        if existing_role:
            raise ValidationError(
                f"Role with name '{role_data['name']}' already exists"
            )

        # Create the role
        role = Role(**role_data)
        created_role = await self.role_repository.create(role)

        return created_role

    async def update_role(self, role_id: str, update_data: Dict[str, Any]) -> Role:
        """
        Update an existing role.

        Args:
            role_id: The role ID
            update_data: Dictionary containing fields to update

        Returns:
            The updated role object

        Raises:
            NotFoundError: If role is not found
            ValidationError: If update data is invalid
        """
        updated_role = await self.role_repository.update(role_id, update_data)
        if not updated_role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return updated_role

    async def delete_role(self, role_id: str) -> bool:
        """
        Delete a role.

        Args:
            role_id: The role ID

        Returns:
            True if role was deleted successfully

        Raises:
            NotFoundError: If role is not found
        """
        # Ensure role exists
        _ = await self.get_role_by_id(role_id)
        # Soft delete the role
        return await self.role_repository.delete(role_id)

    async def assign_permissions_to_role(
        self, role_id: str, permission_ids: List[str]
    ) -> Role:
        """
        Assign permissions to a role.

        Args:
            role_id: The role ID
            permission_ids: List of permission IDs to assign

        Returns:
            The updated role object
        """
        # Validate permission IDs are strings
        if not all(isinstance(pid, str) and pid for pid in permission_ids):
            raise ValidationError("Invalid permission ID format")
        # Update role permissions by IDs
        updated_role = await self.role_repository.update(
            role_id, {"permission_ids": permission_ids}
        )
        if not updated_role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return updated_role
