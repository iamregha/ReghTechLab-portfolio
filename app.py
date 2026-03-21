"""
ReghTechLab Portfolio
=====================
Author  : Abraham Regha
Stack   : Flask + SQLAlchemy + Flask-Login + Jinja2 + Tailwind CSS
"""

import os
from flask import Flask, render_template

# Flask application instance
app = Flask(__name__)

# Configuation
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-fallback-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Routes

@app.route("/")
def index():
    """Homepage - the portfolio landing page"""
    return render_template("index.html")


@app.route("/blog")
def blog():
    """Blog index - lists all published posts."""
    return render_template("blog/index.html")


@app.route("/about")
def about():
    """About page - explains the ReghtechLab mission."""
    return "About page - coming soon!"


# Entry point
if __name__ == "__main__":
    app.run(debug=True)
