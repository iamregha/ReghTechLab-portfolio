"""
config.py
=========
Application configuration classes.
One place for all settings. No configuration
scattered across files.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration — shared by all environments."""

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-change-this")
    if os.environ.get("FLASK_ENV") == "production" and SECRET_KEY == "dev-fallback-change-this":
        raise ValueError("No SECRET_KEY set for production application.")

    # Database
    _db_url = os.environ.get("DATABASE_URL")
    if not _db_url:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("No DATABASE_URL set for production application.")
        _db_url = "sqlite:///portfolio.db"
    SQLALCHEMY_DATABASE_URI      = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

    # Mail Configuration
    MAIL_SERVER       = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT         = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS      = os.environ.get("MAIL_USE_TLS", "True").lower() in ["true", "1", "t"]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False").lower() in ["true", "1", "t"]
    MAIL_USERNAME     = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD     = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@reghtechlab.com")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    MAIL_SUPPRESS_SEND = False
    CONTACT_EMAIL     = os.environ.get("CONTACT_EMAIL", "regha87@gmail.com")

    # Caching — SimpleCache = in-process memory, zero extra infra needed.
    # Can be swapped to RedisCache later with one config line change.
    CACHE_TYPE         = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300   # 5 minutes


class DevelopmentConfig(Config):
    """Local development — debug on, SQLite."""
    DEBUG = True
    RATELIMIT_ENABLED    = False


class ProductionConfig(Config):
    """Railway production — debug off."""
    DEBUG = False


class TestingConfig(Config):
    """pytest — in-memory database, CSRF off."""
    TESTING              = True
    WTF_CSRF_ENABLED     = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED    = False


# Map string names to config classes
# Used in the factory: create_app("production")
config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}