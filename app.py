"""
ReghTechLab Portfolio
=====================
Author  : Abraham Regha
Stack   : Flask + SQLAlchemy + Flask-Login + Jinja2 + Tailwind CSS
"""

import os
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify

# Flask application instance
app = Flask(__name__)

# Configuation
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-fallback-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager(app)

# redirect unauthenticated users
login_manager.login_view = "login"

# to reload user from session
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Datbase Models
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), default="")
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    posts = db.relationship("Post", back_populates="author", lazy="dynamic")
    comments = db.relationship("Comment", back_populates="author", lazy="dynamic")
    likes = db.relationship("Like", back_populates="user", lazy="dynamic")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(400), default="")
    category = db.Column(db.String(80), default="general")
    published = db.Column(db.Boolean, default=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    author = db.relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")
    likes = db.relationship("Like", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()
    
    @property
    def read_time(self):
        words = len(self.content.split())
        minutes = max(1, round(words / 200))
        return f"{minutes} min read"
    
class Comment(db.Model):
    __tablename__ = "comments"

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"),  nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    author = db.relationship("User", back_populates="comments")
    post   = db.relationship("Post", back_populates="comments")


class Like(db.Model):
    __tablename__ = "likes"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    
    __table_args__ = (db.UniqueConstraint("user_id", "post_id"),)

    user = db.relationship("User", back_populates="likes")
    post = db.relationship("Post", back_populates="likes")


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


# Create all tables ONCE
with app.app_context():
    db.create_all()

# Entry point
if __name__ == "__main__":
    app.run(debug=True)
