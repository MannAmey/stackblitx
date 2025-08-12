import pytest
from unittest.mock import Mock, patch
from services.auth_service import AuthService
from services.user_service import UserService

class TestAuthService:
    def test_authenticate_admin_success(self):
        """Test successful admin authentication"""
        auth_service = AuthService()
        
        credentials = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        result = auth_service.authenticate_admin(credentials)
        
        assert result['success'] is True
        assert result['admin']['username'] == 'admin'
        assert 'token' in result

    def test_authenticate_admin_failure(self):
        """Test failed admin authentication"""
        auth_service = AuthService()
        
        credentials = {
            'username': 'admin',
            'password': 'wrongpassword'
        }
        
        with pytest.raises(ValueError):
            auth_service.authenticate_admin(credentials)

class TestUserService:
    @patch('services.user_service.User')
    def test_get_user_by_uid(self, mock_user):
        """Test getting user by UID"""
        # Mock user object
        mock_user_instance = Mock()
        mock_user_instance.uid = '1234567890'
        mock_user_instance.name = 'Test User'
        mock_user_instance.is_active = True
        mock_user_instance.is_blocked = False
        
        # Mock query
        mock_user.objects.return_value.first.return_value = mock_user_instance
        
        user_service = UserService()
        result = user_service.get_user_by_uid('1234567890')
        
        assert result is not None
        assert result.uid == '1234567890'
        assert result.name == 'Test User'

    @patch('services.user_service.User')
    def test_get_user_by_uid_not_found(self, mock_user):
        """Test getting user by UID when user doesn't exist"""
        # Mock empty result
        mock_user.objects.return_value.first.return_value = None
        
        user_service = UserService()
        result = user_service.get_user_by_uid('nonexistent')
        
        assert result is None