import pytest
from unittest.mock import Mock, AsyncMock, patch
from strawberry.types import Info
from app.graphql.mutations.user_mutations import UserMutations

@pytest.mark.asyncio
async def test_delete_user_calls_delete_service_method():
    # Mock info and context
    info_mock = Mock(spec=Info)
    context_mock = Mock()
    info_mock.context = context_mock
    
    # Mock permissions
    context_mock.has_permission = AsyncMock(return_value=True)
    
    # Mock UserService
    with patch("app.graphql.mutations.user_mutations.UserService") as ServiceMock:
        service_instance = ServiceMock.return_value
        service_instance.delete = AsyncMock(return_value=True)
        # Mock deactivate_user to ensure it's NOT called
        service_instance.deactivate_user = AsyncMock(return_value=True)
        
        mutations = UserMutations()
        result = await mutations.delete_user(info_mock, "123")
        
        assert result is True
        service_instance.delete.assert_called_once_with("123")
        # Ensure deactivate_user was NOT called
        service_instance.deactivate_user.assert_not_called()
