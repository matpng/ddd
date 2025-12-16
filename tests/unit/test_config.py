"""
Unit tests for configuration module
"""
import pytest
import os
from config import BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig, get_config


class TestBaseConfig:
    """Tests for BaseConfig class"""
    
    def test_default_values(self):
        """Test default configuration values"""
        assert BaseConfig.APP_NAME == "Orion Octave Cubes"
        assert BaseConfig.VERSION == "1.0.0"
        assert BaseConfig.MAX_ANGLE == 360.0
        assert BaseConfig.MIN_ANGLE == 0.0
    
    def test_environment_variables(self, monkeypatch):
        """Test configuration from environment variables"""
        monkeypatch.setenv('MAX_SIDE_LENGTH', '200')
        monkeypatch.setenv('CACHE_MAX_SIZE', '50')
        
        # Reload config
        from importlib import reload
        import config as config_module
        reload(config_module)
        
        assert config_module.Config.MAX_SIDE_LENGTH == 200.0
        assert config_module.Config.CACHE_MAX_SIZE == 50
    
    def test_validation_success(self):
        """Test successful configuration validation"""
        assert BaseConfig.validate() is True
    
    def test_validation_invalid_side_length(self, monkeypatch):
        """Test validation fails with invalid side length"""
        monkeypatch.setattr(BaseConfig, 'MIN_SIDE_LENGTH', 100)
        monkeypatch.setattr(BaseConfig, 'MAX_SIDE_LENGTH', 50)
        
        with pytest.raises(ValueError, match="MIN_SIDE_LENGTH must be less than MAX_SIDE_LENGTH"):
            BaseConfig.validate()
    
    def test_validation_invalid_port(self, monkeypatch):
        """Test validation fails with invalid port"""
        monkeypatch.setattr(BaseConfig, 'PORT', 99999)
        
        with pytest.raises(ValueError, match="PORT must be between"):
            BaseConfig.validate()


class TestDevelopmentConfig:
    """Tests for DevelopmentConfig"""
    
    def test_debug_enabled(self):
        """Test debug mode is enabled in development"""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False
    
    def test_log_level(self):
        """Test default log level"""
        assert DevelopmentConfig.LOG_LEVEL in ['DEBUG', 'INFO']


class TestProductionConfig:
    """Tests for ProductionConfig"""
    
    def test_debug_disabled(self):
        """Test debug mode is disabled in production"""
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.TESTING is False
    
    def test_stricter_limits(self):
        """Test production has stricter resource limits"""
        assert ProductionConfig.MAX_DISTANCE_PAIRS <= BaseConfig.MAX_DISTANCE_PAIRS
        assert ProductionConfig.MAX_DIRECTION_PAIRS <= BaseConfig.MAX_DIRECTION_PAIRS
    
    def test_secret_key_required(self, monkeypatch):
        """Test production requires SECRET_KEY"""
        # Remove SECRET_KEY
        monkeypatch.delenv('SECRET_KEY', raising=False)
        
        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            ProductionConfig.validate()


class TestTestingConfig:
    """Tests for TestingConfig"""
    
    def test_testing_enabled(self):
        """Test testing mode is enabled"""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is True
    
    def test_lower_limits(self):
        """Test testing config has lower limits for speed"""
        assert TestingConfig.MAX_DISTANCE_PAIRS < BaseConfig.MAX_DISTANCE_PAIRS
        assert TestingConfig.MAX_DIRECTION_PAIRS < BaseConfig.MAX_DIRECTION_PAIRS
    
    def test_cache_disabled(self):
        """Test caching is disabled in testing"""
        assert TestingConfig.CACHE_ENABLED is False


class TestGetConfig:
    """Tests for get_config function"""
    
    def test_get_development_config(self, monkeypatch):
        """Test getting development configuration"""
        monkeypatch.setenv('FLASK_ENV', 'development')
        config = get_config()
        assert config == DevelopmentConfig
    
    def test_get_production_config(self, monkeypatch):
        """Test getting production configuration"""
        monkeypatch.setenv('FLASK_ENV', 'production')
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        config = get_config()
        assert config == ProductionConfig
    
    def test_get_testing_config(self, monkeypatch):
        """Test getting testing configuration"""
        monkeypatch.setenv('FLASK_ENV', 'testing')
        config = get_config()
        assert TestingConfig
    
    def test_default_config(self, monkeypatch):
        """Test default configuration when env not set"""
        monkeypatch.delenv('FLASK_ENV', raising=False)
        config = get_config()
        assert config == DevelopmentConfig
