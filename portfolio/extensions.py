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

db           = SQLAlchemy()
migrate      = Migrate()
login_manager = LoginManager()
csrf         = CSRFProtect()

# Where to redirect unauthenticated users
login_manager.login_view          = "auth.login"
login_manager.login_message_category = "info"