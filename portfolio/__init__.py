"""
portfolio/__init__.py
=====================
Application factory.

create_app() is called once at startup.
It builds the Flask app, configures extensions,
registers blueprints, and returns a ready app.

Why a factory?
  - One function = one place to understand setup
  - Supports multiple configs (dev/prod/test)
  - Tests can create isolated app instances
"""
import os
import cloudinary
from flask import Flask
from flask_migrate import upgrade as flask_upgrade

from .extensions import db, migrate, login_manager, csrf
from config import config


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config[config_name])

    # ── Initialise extensions ──────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Tell Flask-WTF to accept CSRF token from headers
    # This allows AJAX requests to pass the token via X-CSRFToken
    # instead of a hidden form field
    app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]

    # ── Cloudinary ─────────────────────────────────────
    cloudinary.config(
        cloud_name = app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key    = app.config.get("CLOUDINARY_API_KEY"),
        api_secret = app.config.get("CLOUDINARY_API_SECRET"),
    )

    # ── User loader ─────────────────────────────────────
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Register blueprints ─────────────────────────────
    from .auth import auth as auth_blueprint
    from .blog import blog as blog_blueprint
    from .main import main as main_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(blog_blueprint)
    app.register_blueprint(main_blueprint)

    # ── Auto-migrate on startup (dev only) ──────────────
    import sys
    if "pytest" not in sys.modules:
        with app.app_context():
            flask_upgrade()

    return app