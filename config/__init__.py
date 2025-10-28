"""
Configuration module for RentFlow application.

Provides environment-specific configurations:
- DevelopmentConfig: Local Docker development environment
- StagingConfig: Staging environment for testing before production
- ProductionConfig: Production deployment with PostgreSQL
- TestingConfig: Test environment with in-memory database

Usage:
    from config import get_config
    config_class = get_config('development')  # or 'staging', 'production', 'testing'
"""
import os
from decouple import config as env_config


class Config:
    """Base configuration class with common settings across all environments."""

    # Flask Core
    SECRET_KEY = env_config('SECRET_KEY', default='dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # SQLAlchemy Base Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Session Security
    SESSION_COOKIE_SECURE = env_config('SESSION_COOKIE_SECURE', default=False, cast=bool)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = env_config('PERMANENT_SESSION_LIFETIME', default=3600, cast=int)

    # File Uploads
    MAX_CONTENT_LENGTH = env_config('MAX_CONTENT_LENGTH', default=16777216, cast=int)  # 16MB
    UPLOAD_FOLDER = env_config('UPLOAD_FOLDER', default='uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

    # Rate Limiting
    RATELIMIT_STORAGE_URL = env_config('RATELIMIT_STORAGE_URL', default='memory://')
    RATELIMIT_STRATEGY = 'fixed-window'

    # Mail Configuration
    MAIL_SERVER = env_config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = env_config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = env_config('MAIL_USE_TLS', default=True, cast=bool)
    MAIL_USERNAME = env_config('MAIL_USERNAME', default=None)
    MAIL_PASSWORD = env_config('MAIL_PASSWORD', default=None)
    MAIL_DEFAULT_SENDER = env_config('MAIL_DEFAULT_SENDER', default='noreply@rentflow.com')

    # Logging
    LOG_LEVEL = env_config('LOG_LEVEL', default='INFO')
    LOG_FILE = env_config('LOG_FILE', default='logs/rentflow.log')

    @staticmethod
    def init_app(app):
        """Initialize application-specific configuration."""
        pass


class DevelopmentConfig(Config):
    """
    Local development environment configuration.

    Uses Docker Compose with PostgreSQL to match production environment.
    Hot reload enabled for rapid development.
    """

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = env_config(
        'DATABASE_URL',
        default='postgresql://rentflow_dev:rentflow_dev@localhost:5432/rentflow_dev'
    )
    SESSION_COOKIE_SECURE = False

    # Development-specific settings
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False

    # Rate limiting disabled for development
    RATELIMIT_ENABLED = False

    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings."""
        print('🔧 Running in DEVELOPMENT mode')
        print(f'📊 Database: {cls.SQLALCHEMY_DATABASE_URI[:50]}...')


class StagingConfig(Config):
    """
    Staging environment configuration.

    Mirrors production setup but with separate database and relaxed security
    for testing purposes. Deployed on same VPS as production but different ports.

    Note: SESSION_COOKIE_SECURE is False because staging uses HTTP (port 8080)
    without SSL certificates. Production uses HTTPS with Cloudflare SSL.
    """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = env_config('DATABASE_URL', default='postgresql://user:pass@localhost/db')
    SESSION_COOKIE_SECURE = False  # Staging uses HTTP, not HTTPS

    # Staging-specific settings
    TESTING = False
    RATELIMIT_ENABLED = True

    @classmethod
    def init_app(cls, app):
        """Initialize staging-specific settings."""
        # Verify required environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not env_config(var, default=None)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        print('🧪 Running in STAGING mode')
        print('⚠️  This is a testing environment - not for production use')


class ProductionConfig(Config):
    """
    Production environment configuration.

    Fully secured production deployment with PostgreSQL, Redis,
    and all security features enabled.
    """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = env_config('DATABASE_URL', default='postgresql://user:pass@localhost/db')
    SESSION_COOKIE_SECURE = True

    # Production requires strict settings
    RATELIMIT_ENABLED = True

    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        # Verify required environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not env_config(var, default=None)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        print('🚀 Running in PRODUCTION mode')
        print('🔒 Security features: ENABLED')


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

    # SQLite doesn't support PostgreSQL pooling options
    # Override the base class engine options with SQLite-compatible settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False}  # Allow SQLite to work with Flask threading
    }

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    @classmethod
    def init_app(cls, app):
        """Initialize testing-specific settings."""
        print('✅ TEST Loading TestingConfig')
        print('🧪 Running in TESTING mode')


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class by environment name.

    Args:
        config_name: Environment name (development, staging, production, testing)
                    Falls back to FLASK_ENV environment variable, then 'development'

    Returns:
        Configuration class for the specified environment

    Example:
        >>> config = get_config('production')
        >>> app.config.from_object(config)
    """
    if config_name is None:
        config_name = env_config('FLASK_ENV', default='development')

    config_class = config_by_name.get(config_name, config_by_name['default'])

    # Log which config is being used
    env_indicator = {
        'development': '🔧 DEV',
        'staging': '🧪 STAGING',
        'production': '🚀 PROD',
        'testing': '✅ TEST'
    }
    print(f"{env_indicator.get(config_name, '❓')} Loading {config_class.__name__}")

    return config_class
