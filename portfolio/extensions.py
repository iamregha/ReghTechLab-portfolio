"""
extensions.py
=============
Flask extension instances.

Defined here — not in __init__.py — to avoid circular imports.
The factory imports these and calls .init_app(app) on each one.
This is the standard Flask pattern for extensions.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate
from flask_login      import LoginManager
from flask_wtf.csrf   import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from sqlalchemy import MetaData

# Explicit naming convention to prevent SQLite batch modification crashes
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Initialise SQLAlchemy with the naming convention metadata
db            = SQLAlchemy(metadata=MetaData(naming_convention=convention))
migrate       = Migrate()
login_manager = LoginManager()
csrf          = CSRFProtect()
limiter       = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
mail          = Mail()

# Where to redirect unauthenticated users
login_manager.login_view            = "auth.login"
login_manager.login_message_category = "info"