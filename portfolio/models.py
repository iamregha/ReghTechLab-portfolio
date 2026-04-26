"""
models.py
=========
All database models for ReghTechLab.

Kept in one file at this scale — move to models/
subfolder only when this exceeds ~300 lines.
"""
import markdown
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


def utcnow():
    """Callable default for DateTime columns.
    Passed as a callable — not a value — so each row
    gets the time it was created, not the server start time.
    """
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio           = db.Column(db.String(300), default="")
    is_admin      = db.Column(db.Boolean,     default=False)
    joined_at     = db.Column(db.DateTime,    default=utcnow)

    posts    = db.relationship("Post",    back_populates="author", lazy="dynamic")
    comments = db.relationship("Comment", back_populates="author", lazy="dynamic")
    likes    = db.relationship("Like",    back_populates="user",   lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_liked(self, post):
        return db.session.execute(
            db.select(Like).filter_by(
                user_id=self.id,
                post_id=post.id
            )
        ).scalar_one_or_none() is not None


class Post(db.Model):
    __tablename__ = "posts"

    id         = db.Column(db.Integer,     primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    slug       = db.Column(db.String(220), unique=True, nullable=False)
    content    = db.Column(db.Text,        nullable=False)
    excerpt    = db.Column(db.String(400), default="")
    category   = db.Column(db.String(80),  default="General")
    published  = db.Column(db.Boolean,     default=True)
    cover_url  = db.Column(db.String(500), default="")
    author_id  = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime,    default=utcnow)

    author   = db.relationship("User",    back_populates="posts")
    comments = db.relationship("Comment", back_populates="post",
                               cascade="all, delete-orphan", lazy="dynamic")
    likes    = db.relationship("Like",    back_populates="post",
                               cascade="all, delete-orphan", lazy="dynamic")

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def read_time(self):
        words   = len(self.content.split())
        minutes = max(1, round(words / 200))
        return f"{minutes} min read"

    @property
    def rendered_content(self):
        return markdown.markdown(
            self.content,
            extensions=["fenced_code", "tables", "nl2br"]
        )


class Comment(db.Model):
    __tablename__ = "comments"

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text,    nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"),  nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

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
    