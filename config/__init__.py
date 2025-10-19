"""
Configuration module for RentFlow application.

Provides environment-specific configurations:
- DevelopmentConfig: Local development with SQLite
- ProductionConfig: Production deployment with PostgreSQL
- TestingConfig: Test environment with in-memory database
"""
import os
from decouple import config as env_config


class Config:
    """Base configuration class with common settings."""

    # Flask
    SECRET_KEY = env_config('SECRET_KEY', default='dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
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
    """Development environment configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = env_config(
        'DATABASE_URL',
        default='sqlite:///database.db'
    )
    SESSION_COOKIE_SECURE = False

    # Development-specific settings
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False

    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings."""
        print('🔧 Running in DEVELOPMENT mode')


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = env_config('DATABASE_URL')
    SESSION_COOKIE_SECURE = True

    # Production requires these to be set
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        # Verify required environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not env_config(var, default=None)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        print('🚀 Running in PRODUCTION mode')


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    @classmethod
    def init_app(cls, app):
        """Initialize testing-specific settings."""
        print('🧪 Running in TESTING mode')


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class by environment name.

    Args:
        config_name: Environment name (development, production, testing)
        Falls back to FLASK_ENV environment variable, then 'default'

    Returns:
        Configuration class for the specified environment
    """
    if config_name is None:
        config_name = env_config('FLASK_ENV', default='development')

    return config_by_name.get(config_name, config_by_name['default'])
