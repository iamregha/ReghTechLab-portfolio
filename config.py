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

    # Database
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI      = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")


class DevelopmentConfig(Config):
    """Local development — debug on, SQLite."""
    DEBUG = True


class ProductionConfig(Config):
    """Railway production — debug off."""
    DEBUG = False


class TestingConfig(Config):
    """pytest — in-memory database, CSRF off."""
    TESTING              = True
    WTF_CSRF_ENABLED     = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Map string names to config classes
# Used in the factory: create_app("production")
config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}