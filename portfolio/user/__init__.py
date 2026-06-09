"""
user/__init__.py
================
Initialises the 'user' blueprint package.
This pattern keeps import clean — the blueprint object
is created here and routes are added in routes.py.
"""
from flask import Blueprint

# Create the blueprint. url_prefix means every route in this
# blueprint automatically starts with /user, keeping URLs tidy.
user_blueprint = Blueprint("user", __name__, url_prefix="/user")

# Import routes AFTER creating the blueprint to avoid circular imports.
# Python executes this import last, so the blueprint object already exists
# when routes.py tries to decorate functions with @user_blueprint.route(...)
from . import routes  # noqa: F401, E402
