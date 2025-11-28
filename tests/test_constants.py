"""
Unit tests for constants module.
"""
import pytest
from app.core.constants import (
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES,
    DEFAULT_GROUPS
)


class TestDefaultPermissions:
    """Test default permissions constants."""
    
    def test_permissions_exist(self):
        """Test that default permissions are defined."""
        assert DEFAULT_PERMISSIONS is not None
        assert isinstance(DEFAULT_PERMISSIONS, dict)
        assert len(DEFAULT_PERMISSIONS) > 0
    
    def test_user_permissions(self):
        """Test user-related permissions."""
        assert "users:read" in DEFAULT_PERMISSIONS
        assert "users:update" in DEFAULT_PERMISSIONS
        assert "users:delete" in DEFAULT_PERMISSIONS
    
    def test_role_permissions(self):
        """Test role-related permissions."""
        assert "roles:read" in DEFAULT_PERMISSIONS
        assert "roles:update" in DEFAULT_PERMISSIONS
        assert "roles:delete" in DEFAULT_PERMISSIONS
    
    def test_permission_descriptions(self):
        """Test that permissions have descriptions."""
        for name, description in DEFAULT_PERMISSIONS.items():
            assert isinstance(name, str)
            assert isinstance(description, str)
            assert len(description) > 0


class TestDefaultRoles:
    """Test default roles constants."""
    
    def test_roles_exist(self):
        """Test that default roles are defined."""
        assert DEFAULT_ROLES is not None
        assert isinstance(DEFAULT_ROLES, dict)
        assert len(DEFAULT_ROLES) > 0
    
    def test_superadmin_role(self):
        """Test superadmin role configuration."""
        assert "superadmin" in DEFAULT_ROLES
        superadmin = DEFAULT_ROLES["superadmin"]
        
        assert "description" in superadmin
        assert "permissions" in superadmin
        assert "is_system_role" in superadmin
        assert superadmin["is_system_role"] is True
    
    def test_admin_role(self):
        """Test admin role configuration."""
        assert "admin" in DEFAULT_ROLES
        admin = DEFAULT_ROLES["admin"]
        
        assert "description" in admin
        assert "permissions" in admin
        assert isinstance(admin["permissions"], list)
    
    def test_user_role(self):
        """Test user role configuration."""
        assert "user" in DEFAULT_ROLES
        user = DEFAULT_ROLES["user"]
        
        assert "description" in user
        assert "permissions" in user
    
    def test_role_structure(self):
        """Test that all roles have required structure."""
        for role_name, role_data in DEFAULT_ROLES.items():
            assert "description" in role_data
            assert "permissions" in role_data
            assert "is_system_role" in role_data
            assert isinstance(role_data["permissions"], list)
            assert isinstance(role_data["is_system_role"], bool)


class TestDefaultGroups:
    """Test default groups constants."""
    
    def test_groups_exist(self):
        """Test that default groups are defined."""
        assert DEFAULT_GROUPS is not None
        assert isinstance(DEFAULT_GROUPS, dict)
        assert len(DEFAULT_GROUPS) > 0
    
    def test_administrators_group(self):
        """Test administrators group configuration."""
        assert "administrators" in DEFAULT_GROUPS
        administrators = DEFAULT_GROUPS["administrators"]
        
        assert "description" in administrators
        assert "is_system_group" in administrators
        assert administrators["is_system_group"] is True
    
    def test_users_group(self):
        """Test users group configuration."""
        assert "users" in DEFAULT_GROUPS
        users = DEFAULT_GROUPS["users"]
        
        assert "description" in users
        assert "is_system_group" in users
    
    def test_group_structure(self):
        """Test that all groups have required structure."""
        for group_name, group_data in DEFAULT_GROUPS.items():
            assert "description" in group_data
            assert "is_system_group" in group_data
            assert isinstance(group_data["is_system_group"], bool)
            
            if "metadata" in group_data:
                assert isinstance(group_data["metadata"], dict)


class TestConstantsIntegrity:
    """Test integrity between constants."""
    
    def test_role_permissions_exist(self):
        """Test that role permissions reference existing permissions."""
        for role_name, role_data in DEFAULT_ROLES.items():
            for permission in role_data["permissions"]:
                assert permission in DEFAULT_PERMISSIONS, \
                    f"Role '{role_name}' references non-existent permission '{permission}'"
    
    def test_no_duplicate_permissions(self):
        """Test that there are no duplicate permission names."""
        permission_names = list(DEFAULT_PERMISSIONS.keys())
        assert len(permission_names) == len(set(permission_names))
    
    def test_no_duplicate_roles(self):
        """Test that there are no duplicate role names."""
        role_names = list(DEFAULT_ROLES.keys())
        assert len(role_names) == len(set(role_names))
    
    def test_no_duplicate_groups(self):
        """Test that there are no duplicate group names."""
        group_names = list(DEFAULT_GROUPS.keys())
        assert len(group_names) == len(set(group_names))
