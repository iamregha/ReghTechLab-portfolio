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
from flask import app
import os
import cloudinary
from flask import Flask
from flask_migrate import upgrade as flask_upgrade

from .extensions import db, migrate, login_manager, csrf, limiter, mail
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
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

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
    from .errors import errors as errors_blueprint
    from .user import user_blueprint  # New in Step 2: User Profiles

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(blog_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(errors_blueprint)
    app.register_blueprint(user_blueprint)  # routes live at /user/...

    from .models import Notification
    from flask_login import current_user

    
    @app.context_processor
    def inject_unread_notifications():
        unread_count = 0
        if current_user.is_authenticated:
            try:
                count = db.session.execute(
                db.select(db.func.count(Notification.id))
                .filter_by(user_id=current_user.id, is_read=False)
                ).scalar()
                unread_count = count or 0
            except Exception:
                unread_count = 0  # DB not ready in tests
        return {"unread_count": unread_count}
    
    return app