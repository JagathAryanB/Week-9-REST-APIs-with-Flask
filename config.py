import os
from datetime import timedelta
from dotenv import load_dotenv

# Disable C extensions for Windows Application Control environments
os.environ.setdefault('DISABLE_SQLALCHEMY_CEXT', '1')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day; 50 per hour')
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    API_TITLE = "Task Management REST API"
    API_VERSION = "v1"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'task_management_dev.db')}"
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    RATELIMIT_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'task_management_prod.db')}"
    )


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

