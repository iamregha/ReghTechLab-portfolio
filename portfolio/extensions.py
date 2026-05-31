"""
extensions.py
=============
Flask extension instances.

Defined here — not in __init__.py — to avoid circular imports.
The factory imports these and calls .init_app(app) on each one.
This is the standard Flask pattern for extensions.
"""
import cloudinary
from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate
from flask_login      import LoginManager
from flask_wtf.csrf   import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db           = SQLAlchemy()
migrate      = Migrate()
login_manager = LoginManager()
csrf         = CSRFProtect()
limiter      = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# Where to redirect unauthenticated users
login_manager.login_view          = "auth.login"
login_manager.login_message_category = "info"