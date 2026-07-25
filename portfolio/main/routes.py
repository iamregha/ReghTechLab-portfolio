"""
main/routes.py
==============
Portfolio pages: homepage, about, contact.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from sqlalchemy.exc import ProgrammingError
from flask_login import current_user

from ..extensions import db, cache
from ..models import Post
from portfolio.email_utils import send_contact_email

CATEGORIES = [
    "Python & Backend",
    "Industrial Automation",
    "Retail Operations",
    "IoT & Embedded",
    "Maintenance & Reliability",
    "Tutorials",
]


main = Blueprint("main", __name__)

@main.route("/")
@cache.cached(timeout=300, key_prefix="homepage", unless=lambda: current_user.is_authenticated)
def index():
    try:
        recent_posts = db.session.execute(
            db.select(Post)
            .filter_by(published=True)
            .order_by(Post.created_at.desc())
            .limit(3)
        ).scalars().all()
    except Exception:
        db.session.rollback()
        recent_posts = []

    return render_template("index.html", recent_posts=recent_posts)


@main.route("/robots.txt")
def robots():
    # return send_from_directory(os.path.join(main.root_path, "..", "static"), "robots.txt")
    return current_app.send_static_file("robots.txt")


@main.route("/sitemap.xml")
def sitemap():
    posts = db.session.execute(
        db.select(Post).filter_by(published=True)
    ).scalars().all()
    response = render_template("sitemap.xml", posts=posts)
    return response, 200, {"Content-Type": "application/xml"}

@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name",    "").strip()
        email   = request.form.get("email",   "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Basic server-side validation (defence-in-depth beyond HTML required)
        if not all([name, email, message]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("main.contact"))

        if len(message) > 5000:
            flash("Message is too long (max 5000 characters).", "error")
            return redirect(url_for("main.contact"))

        # Fire email asynchronously — does not block the request
        try:
            send_contact_email(name, email, subject, message)
            flash("Message sent! I\u2019ll get back to you within 24 hours.", "success")
        except Exception:
            flash("Message received, but email delivery is currently unavailable.", "info")

        return redirect(url_for("main.contact"))

    return render_template("contact.html")
