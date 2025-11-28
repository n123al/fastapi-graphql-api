"""
Unit tests for configuration module.
"""
import pytest
import os
from app.core.config import Settings


class TestSettings:
    """Test application settings."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        
        assert settings is not None
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'PORT')
    
    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        
        assert settings.APP_NAME == "FastAPI GraphQL API"
        assert isinstance(settings.DEBUG, bool)
        assert isinstance(settings.PORT, int)
        assert settings.PORT > 0
    
    def test_database_settings(self):
        """Test database configuration."""
        settings = Settings()
        
        assert hasattr(settings, 'MONGODB_URL')
        assert hasattr(settings, 'DATABASE_NAME')
        assert isinstance(settings.MONGODB_URL, str)
        assert isinstance(settings.DATABASE_NAME, str)
    
    def test_security_settings(self):
        """Test security configuration."""
        settings = Settings()
        
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_cors_settings(self):
        """Test CORS configuration."""
        settings = Settings()
        
        assert hasattr(settings, 'ALLOWED_HOSTS')
        assert isinstance(settings.ALLOWED_HOSTS, list)
    
    def test_authentication_settings(self):
        """Test authentication configuration."""
        settings = Settings()
        
        assert hasattr(settings, 'REQUIRE_AUTHENTICATION')
        assert hasattr(settings, 'RATE_LIMIT_PER_MINUTE')
        assert isinstance(settings.REQUIRE_AUTHENTICATION, bool)
        assert settings.RATE_LIMIT_PER_MINUTE > 0
