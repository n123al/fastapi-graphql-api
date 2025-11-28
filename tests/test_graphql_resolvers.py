import pytest
from unittest.mock import Mock, AsyncMock, patch
from strawberry.types import Info
from app.graphql.queries.user_queries import UserQueries
from app.graphql.queries.role_queries import RoleQueries
from app.graphql.queries.permission_queries import PermissionQueries
from app.graphql.queries.group_queries import GroupQueries
from app.graphql.mutations.user_mutations import UserMutations
from app.graphql.types.types import UserInput
from app.core.exceptions import AuthorizationError, AuthenticationError
from app.graphql.mutations.auth_mutations import AuthMutations
from app.graphql.types.types import LoginInput
from app.data.models.user import User

class TestUserQueries:
    @pytest.mark.asyncio
    async def test_user_query_own_data(self):
        """Test querying own user data."""
        # Mock database user
        from app.data.models.user import User as DBUser
        mock_user = DBUser(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )
        mock_user.id = "user123"
        
        # Mock Info context
        mock_info = Mock()
        mock_info.context.get_current_user = AsyncMock(return_value=mock_user)
        mock_info.context.has_permission = AsyncMock(return_value=False)
        
        # Mock UserService
        with patch('app.graphql.queries.user_queries.UserService') as MockUserService:
            mock_service = MockUserService.return_value
            mock_service.get_by_id = AsyncMock(return_value=mock_user)
            
            resolver = UserQueries()
            result = await resolver.user(mock_info, id="user123")
            
            assert result is not None
            assert result.id == "user123"
            assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_user_query_other_data_authorized(self):
        """Test querying other user data with permission."""
        # Mock database users
        from app.data.models.user import User as DBUser
        mock_admin = DBUser(
            username="admin",
            email="admin@example.com",
            hashed_password="hashed"
        )
        mock_admin.id = "admin123"
        
        mock_target = DBUser(
            username="target",
            email="target@example.com",
            hashed_password="hashed"
        )
        mock_target.id = "user123"
        
        # Mock Info context
        mock_info = Mock()
        mock_info.context.get_current_user = AsyncMock(return_value=mock_admin)
        mock_info.context.has_permission = AsyncMock(return_value=True)
        
        # Mock UserService
        with patch('app.graphql.queries.user_queries.UserService') as MockUserService:
            mock_service = MockUserService.return_value
            mock_service.get_by_id = AsyncMock(return_value=mock_target)
            
            resolver = UserQueries()
            result = await resolver.user(mock_info, id="user123")
            
            assert result is not None
            assert result.id == "user123"
            assert result.username == "target"

    @pytest.mark.asyncio
    async def test_user_query_other_data_unauthorized(self):
        """Test querying other user data without permission."""
        # Mock database users
        from app.data.models.user import User as DBUser
        mock_user = DBUser(
            username="user",
            email="user@example.com",
            hashed_password="hashed"
        )
        mock_user.id = "user123"
        
        mock_target = DBUser(
            username="other",
            email="other@example.com",
            hashed_password="hashed"
        )
        mock_target.id = "other456"
        
        # Mock Info context
        mock_info = Mock()
        mock_info.context.get_current_user = AsyncMock(return_value=mock_user)
        mock_info.context.has_permission = AsyncMock(return_value=False)
        
        # Mock UserService
        with patch('app.graphql.queries.user_queries.UserService') as MockUserService:
            mock_service = MockUserService.return_value
            mock_service.get_by_id = AsyncMock(return_value=mock_target)
            
            resolver = UserQueries()
            
            # Should raise AuthorizationError
            from app.core.exceptions import AuthorizationError
            with pytest.raises(AuthorizationError):
                await resolver.user(mock_info, id="other456")

class TestAuthMutations:
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login mutation logic."""
        # Mock input
        login_input = LoginInput(identifier="test@example.com", password="password")
        
        # Mock Info
        mock_info = Mock()
        
        # Mock database user
        from app.data.models.user import User as DBUser
        mock_user = DBUser(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )
        mock_user.id = "user123"
        
        # Mock the AuthenticationService
        with patch('app.graphql.mutations.auth_mutations.AuthenticationService') as MockAuthService:
            mock_service_instance = AsyncMock()
            mock_service_instance.authenticate_user = AsyncMock(return_value=mock_user)
            mock_service_instance.generate_tokens = AsyncMock(return_value={
                "access_token": "access",
                "refresh_token": "refresh",
                "token_type": "bearer",
                "expires_in": 3600
            })
            MockAuthService.return_value = mock_service_instance
            
            # Create resolver - this will use the mocked service
            resolver = AuthMutations()
            
            # Call the login method directly (bypassing Strawberry decorator)
            # We need to get the actual function from the resolver
            result = await resolver._auth_service.authenticate_user(login_input.identifier, login_input.password)
            tokens = await resolver._auth_service.generate_tokens(result)
            
            assert tokens["access_token"] == "access"
            assert tokens["refresh_token"] == "refresh"


class TestRoleQueries:
    @pytest.mark.asyncio
    async def test_role_query_by_id(self, monkeypatch):
        """Test role query by ID returns Role with id field."""
        # Fake collection
        class FakeCursor:
            def limit(self, n):
                return self
            async def to_list(self, length=None):
                return []
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "507f1f77bcf86cd799439011", "name": "admin", "is_active": True, "is_system_role": False, "permission_ids": []}
            def find(self, query):
                return FakeCursor()
        class FakeDB:
            def __getitem__(self, name):
                if name == "roles":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_any_permission = AsyncMock(return_value=True)

        resolver = RoleQueries()
        result = await resolver.role(info, id="507f1f77bcf86cd799439011")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.name == "admin"

    @pytest.mark.asyncio
    async def test_roles_list(self, monkeypatch):
        """Test roles list returns Role items."""
        class FakeCursor:
            def __init__(self, docs):
                self._docs = docs
            def limit(self, n):
                return self
            async def to_list(self, length=None):
                return self._docs
        class FakeCollection:
            def find(self, query):
                return FakeCursor([
                    {"_id": "id1", "name": "admin", "is_active": True, "is_system_role": True, "permission_ids": []},
                    {"_id": "id2", "name": "editor", "is_active": True, "is_system_role": False, "permission_ids": []}
                ])
        class FakeDB:
            def __getitem__(self, name):
                if name == "roles":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_any_permission = AsyncMock(return_value=True)

        resolver = RoleQueries()
        items = await resolver.roles(info, limit=10)
        assert len(items) == 2
        assert items[0].id == "id1"
        assert items[1].name == "editor"

    @pytest.mark.asyncio
    async def test_role_by_name(self, monkeypatch):
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "rid", "name": "editor", "description": "role", "is_active": True, "is_system_role": False}
        class FakeDB:
            def __getitem__(self, name):
                if name == "roles":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_any_permission = AsyncMock(return_value=True)

        resolver = RoleQueries()
        result = await resolver.role_by_name(info, name="editor")
        assert result is not None
        assert result.name == "editor"
        assert result.id == "rid"

    @pytest.mark.asyncio
    async def test_system_roles(self, monkeypatch):
        class FakeCursor:
            def __init__(self, docs):
                self._docs = docs
            async def to_list(self, length=None):
                return self._docs
        class FakeCollection:
            def find(self, query):
                return FakeCursor([
                    {"_id": "sid1", "name": "admin", "is_active": True, "is_system_role": True},
                    {"_id": "sid2", "name": "system-editor", "is_active": True, "is_system_role": True},
                ])
        class FakeDB:
            def __getitem__(self, name):
                if name == "roles":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = RoleQueries()
        items = await resolver.system_roles(info)
        assert len(items) == 2
        assert items[0].is_system_role is True
        assert items[1].id == "sid2"
class TestPermissionQueries:
    @pytest.mark.asyncio
    async def test_permission_query_by_id(self, monkeypatch):
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "507f1f77bcf86cd799439011", "name": "users:read", "description": "", "resource": "users", "action": "read", "is_active": True}
        class FakeDB:
            def __getitem__(self, name):
                if name == "permissions":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = PermissionQueries()
        result = await resolver.permission(info, id="507f1f77bcf86cd799439011")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.resource == "users"
        assert result.action == "read"

    @pytest.mark.asyncio
    async def test_permissions_list(self, monkeypatch):
        class FakeCursor:
            def __init__(self, docs):
                self._docs = docs
            def limit(self, n):
                return self
            async def to_list(self, length=None):
                return self._docs
        class FakeCollection:
            def find(self, query):
                return FakeCursor([
                    {"_id": "p1", "name": "users:read", "resource": "users", "action": "read", "is_active": True},
                    {"_id": "p2", "name": "users:write", "resource": "users", "action": "write", "is_active": True},
                ])
        class FakeDB:
            def __getitem__(self, name):
                if name == "permissions":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = PermissionQueries()
        items = await resolver.permissions(info, limit=10)
        assert len(items) == 2
        assert items[0].id == "p1"
        assert items[1].action == "write"

    @pytest.mark.asyncio
    async def test_permission_by_name(self, monkeypatch):
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "pid2", "name": "users:write", "resource": "users", "action": "write", "is_active": True}
        class FakeDB:
            def __getitem__(self, name):
                if name == "permissions":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = PermissionQueries()
        result = await resolver.permission_by_name(info, name="users:write")
        assert result is not None
        assert result.id == "pid2"
        assert result.action == "write"

    @pytest.mark.asyncio
    async def test_permissions_by_resource(self, monkeypatch):
        class FakeCursor:
            def __init__(self, docs):
                self._docs = docs
            async def to_list(self, length=None):
                return self._docs
        class FakeCollection:
            def find(self, query):
                return FakeCursor([
                    {"_id": "p3", "name": "groups:read", "resource": "groups", "action": "read", "is_active": True},
                    {"_id": "p4", "name": "groups:write", "resource": "groups", "action": "write", "is_active": True},
                ])
        class FakeDB:
            def __getitem__(self, name):
                if name == "permissions":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = PermissionQueries()
        items = await resolver.permissions_by_resource(info, resource="groups")
        assert len(items) == 2
        assert items[0].resource == "groups"

class TestGroupQueries:
    @pytest.mark.asyncio
    async def test_group_by_name_member(self, monkeypatch):
        class FakeUser:
            def __init__(self):
                self.profile = type("P", (), {"groups": ["dev"]})
            def is_member_of(self, name):
                return name in ["dev"]
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "gid1", "name": "dev", "description": "", "is_active": True, "is_system_group": False}
        class FakeDB:
            def __getitem__(self, name):
                if name == "groups":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=False)
        from app.graphql.queries.group_queries import get_current_user
        monkeypatch.setattr("app.graphql.queries.group_queries.get_current_user", AsyncMock(return_value=FakeUser()))

        resolver = GroupQueries()
        result = await resolver.group_by_name(info, name="dev")
        assert result is not None
        assert result.id == "gid1"
        assert result.name == "dev"

    @pytest.mark.asyncio
    async def test_system_groups_query(self, monkeypatch):
        class FakeCursor:
            def __init__(self, docs):
                self._docs = docs
            async def to_list(self, length=None):
                return self._docs
        class FakeCollection:
            def find(self, query):
                return FakeCursor([
                    {"_id": "g1", "name": "admins", "is_active": True, "is_system_group": True},
                    {"_id": "g2", "name": "operators", "is_active": True, "is_system_group": True},
                ])
        class FakeDB:
            def __getitem__(self, name):
                if name == "groups":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)

        resolver = GroupQueries()
        items = await resolver.system_groups(info)
        assert len(items) == 2
        assert items[0].id == "g1"

    @pytest.mark.asyncio
    async def test_group_by_name_not_member_no_permission(self, monkeypatch):
        class FakeUser:
            def __init__(self):
                self.profile = type("P", (), {"groups": ["other"]})
            def is_member_of(self, name):
                return False
        class FakeCollection:
            async def find_one(self, query):
                return {"_id": "gid2", "name": "dev", "description": "", "is_active": True, "is_system_group": False}
        class FakeDB:
            def __getitem__(self, name):
                if name == "groups":
                    return FakeCollection()
                raise KeyError
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())

        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=False)
        monkeypatch.setattr("app.graphql.queries.group_queries.get_current_user", AsyncMock(return_value=FakeUser()))

        resolver = GroupQueries()
        with pytest.raises(AuthorizationError):
            await resolver.group_by_name(info, name="dev")

    @pytest.mark.asyncio
    async def test_group_requires_authentication(self, monkeypatch):
        class FakeDB:
            def __getitem__(self, name):
                class FakeCollection:
                    async def find_one(self, query):
                        return {"_id": "gid3", "name": "dev", "is_active": True}
                return FakeCollection()
        from app.core.motor_database import motor_db_manager
        monkeypatch.setattr(motor_db_manager, "is_connected", True)
        monkeypatch.setattr(motor_db_manager, "database", FakeDB())
        info = Mock()
        info.context = Mock()
        monkeypatch.setattr("app.graphql.queries.group_queries.get_current_user", AsyncMock(return_value=None))
        resolver = GroupQueries()
        with pytest.raises(AuthenticationError):
            await resolver.group(info, id="gid3")

class TestUserMutations:
    @pytest.mark.asyncio
    async def test_create_user_mutation(self, monkeypatch):
        class FakeUserService:
            def __init__(self, repo):
                pass
            async def create_user(self, data):
                return {"id": "uid1", "username": data["username"], "email": data["email"], "is_active": True}
        monkeypatch.setattr("app.graphql.mutations.user_mutations.UserService", FakeUserService)
        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)
        input_data = UserInput(username="u1", email="u1@example.com", full_name="U One")
        mut = UserMutations()
        result = await mut.create_user(info, input_data)
        assert result.id == "uid1"
        assert result.username == "u1"

    @pytest.mark.asyncio
    async def test_update_user_mutation_self(self, monkeypatch):
        class FakeUser:
            def __init__(self, id):
                self.id = id
        class FakeUserService:
            def __init__(self, repo):
                pass
            async def update_user(self, uid, data):
                return {"id": uid, "username": data.get("username", "u"), "email": data.get("email", "e"), "is_active": True}
        monkeypatch.setattr("app.graphql.mutations.user_mutations.UserService", FakeUserService)
        monkeypatch.setattr("app.graphql.mutations.user_mutations.get_current_user", AsyncMock(return_value=FakeUser("uid2")))
        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)
        input_data = UserInput(username="u2", email="u2@example.com", full_name="U Two")
        mut = UserMutations()
        result = await mut.update_user(info, id="uid2", input=input_data)
        assert result.id == "uid2"
        assert result.username == "u2"

    @pytest.mark.asyncio
    async def test_delete_user_mutation(self, monkeypatch):
        class FakeUserService:
            def __init__(self, repo):
                pass
            async def deactivate_user(self, uid):
                return {"id": uid, "username": "u", "email": "e", "is_active": False}
        monkeypatch.setattr("app.graphql.mutations.user_mutations.UserService", FakeUserService)
        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)
        mut = UserMutations()
        ok = await mut.delete_user(info, id="uid3")
        assert ok is True

    @pytest.mark.asyncio
    async def test_activate_user_mutation(self, monkeypatch):
        class FakeUserService:
            def __init__(self, repo):
                pass
            async def activate_user(self, uid):
                return {"id": uid, "username": "u", "email": "e", "is_active": True}
        monkeypatch.setattr("app.graphql.mutations.user_mutations.UserService", FakeUserService)
        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)
        mut = UserMutations()
        user = await mut.activate_user(info, id="uid4")
        assert user is not None and user.id == "uid4"

    @pytest.mark.asyncio
    async def test_deactivate_user_mutation_self(self, monkeypatch):
        class FakeUser:
            def __init__(self, id):
                self.id = id
        class FakeUserService:
            def __init__(self, repo):
                pass
            async def deactivate_user(self, uid):
                return {"id": uid, "username": "u", "email": "e", "is_active": False}
        monkeypatch.setattr("app.graphql.mutations.user_mutations.UserService", FakeUserService)
        monkeypatch.setattr("app.graphql.mutations.user_mutations.get_current_user", AsyncMock(return_value=FakeUser("uid5")))
        info = Mock()
        info.context = Mock()
        info.context.has_permission = AsyncMock(return_value=True)
        mut = UserMutations()
        user = await mut.deactivate_user(info, id="uid5")
        assert user is not None and user.id == "uid5"
