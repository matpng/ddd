#!/usr/bin/env python3
"""
Configuration Management
Centralized configuration with environment variable support
"""

import os
import secrets
from pathlib import Path


class BaseConfig:
    """Base configuration with common settings."""
    
    # Application
    APP_NAME = "Orion Octave Cubes"
    VERSION = "1.0.0"
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Server
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT') or os.environ.get('FLASK_PORT', 5000))  # Render uses PORT
    
    # Analysis constraints
    MAX_SIDE_LENGTH = float(os.environ.get('MAX_SIDE_LENGTH', 100))
    MIN_SIDE_LENGTH = float(os.environ.get('MIN_SIDE_LENGTH', 0.01))
    MAX_ANGLE = 360.0
    MIN_ANGLE = 0.0
    MAX_DISTANCE_PAIRS = int(os.environ.get('MAX_DISTANCE_PAIRS', 100000))
    MAX_DIRECTION_PAIRS = int(os.environ.get('MAX_DIRECTION_PAIRS', 100000))
    
    # Default analysis parameters
    DEFAULT_SIDE = 2.0
    DEFAULT_ANGLE = 30.0
    DEFAULT_DISTANCE_PAIRS = 20000
    DEFAULT_DIRECTION_PAIRS = 8000
    
    # Cache settings
    CACHE_ENABLED = True
    CACHE_MAX_SIZE = int(os.environ.get('CACHE_MAX_SIZE', 100))
    
    # Paths
    BASE_DIR = Path(__file__).parent
    STATIC_DIR = BASE_DIR / 'static'
    TEMPLATES_DIR = BASE_DIR / 'templates'
    TEST_RESULTS_DIR = BASE_DIR / 'test_results'
    
    @classmethod
    def validate(cls):
        """Validate configuration values."""
        errors = []
        
        if cls.MIN_SIDE_LENGTH >= cls.MAX_SIDE_LENGTH:
            errors.append("MIN_SIDE_LENGTH must be less than MAX_SIDE_LENGTH")
        
        if cls.MIN_ANGLE >= cls.MAX_ANGLE:
            errors.append("MIN_ANGLE must be less than MAX_ANGLE")
        
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append(f"PORT must be between 1 and 65535, got {cls.PORT}")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True


class DevelopmentConfig(BaseConfig):
    """Development configuration with debugging enabled."""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')


class ProductionConfig(BaseConfig):
    """Production configuration with security hardening."""
    DEBUG = False
    TESTING = False
    
    # Stricter limits for production
    MAX_DISTANCE_PAIRS = int(os.environ.get('MAX_DISTANCE_PAIRS', 50000))
    MAX_DIRECTION_PAIRS = int(os.environ.get('MAX_DIRECTION_PAIRS', 25000))
    
    # Production logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # Require explicit secret key in production
    @classmethod
    def validate(cls):
        """Additional production validation."""
        super().validate()
        
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        return True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    
    # Lower limits for faster testing
    MAX_DISTANCE_PAIRS = 5000
    MAX_DIRECTION_PAIRS = 2000
    DEFAULT_DISTANCE_PAIRS = 1000
    DEFAULT_DIRECTION_PAIRS = 500
    
    # Disable caching in tests
    CACHE_ENABLED = False


# Configuration selector
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment."""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config_map.get(env, DevelopmentConfig)
    config_class.validate()
    
    return config_class


# Export current configuration
Config = get_config()


if __name__ == '__main__':
    # Test configuration
    print("=" * 70)
    print("Configuration Test")
    print("=" * 70)
    
    for env_name in ['development', 'production', 'testing']:
        print(f"\n{env_name.upper()} Configuration:")
        print("-" * 70)
        
        try:
            if env_name == 'production':
                # Skip production validation if SECRET_KEY not set
                if not os.environ.get('SECRET_KEY'):
                    print("  ⚠️  Skipping production validation (SECRET_KEY not set)")
                    continue
            
            cfg = get_config(env_name)
            print(f"  ✓ DEBUG: {cfg.DEBUG}")
            print(f"  ✓ HOST: {cfg.HOST}:{cfg.PORT}")
            print(f"  ✓ Side range: {cfg.MIN_SIDE_LENGTH} - {cfg.MAX_SIDE_LENGTH}")
            print(f"  ✓ Max pairs: dist={cfg.MAX_DISTANCE_PAIRS}, dir={cfg.MAX_DIRECTION_PAIRS}")
            print(f"  ✓ Cache: {cfg.CACHE_ENABLED} (max {cfg.CACHE_MAX_SIZE})")
            
        except ValueError as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print("All configurations validated successfully!")
    print("=" * 70)
