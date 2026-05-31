"""
errors.py
=========
Global error handlers for the application.
"""
from flask import Blueprint, render_template
import logging

errors = Blueprint("errors", __name__)

# Basic logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@errors.app_errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403

@errors.app_errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@errors.app_errorhandler(429)
def ratelimit_handler(e):
    return render_template("errors/429.html", description=e.description), 429

@errors.app_errorhandler(500)
def internal_server_error(e):
    logging.exception("An unhandled exception occurred.")
    return render_template("errors/500.html"), 500
