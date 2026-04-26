"""
main/routes.py
==============
Portfolio pages: homepage, about, contact.
"""
from flask import Blueprint, render_template
from ..models import Post
from ..extensions import db

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
def index():
    recent_posts = db.session.execute(
        db.select(Post)
        .filter_by(published=True)
        .order_by(Post.created_at.desc())
        .limit(3)
    ).scalars().all()
    return render_template("index.html", recent_posts=recent_posts)


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/contact")
def contact():
    return render_template("contact.html")