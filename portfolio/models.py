"""
models.py
=========
All database models for ReghTechLab.

Kept in one file at this scale — move to models/
subfolder only when this exceeds ~300 lines.
"""
import hashlib
import markdown
import bleach
from datetime import datetime, timezone
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

from .extensions import db

import re

# Matches a line that is ENTIRELY two or more "#word" tokens — e.g. "#coding #python"
# Deliberately requires 2+ tags so a genuine single "# Heading" is never touched.
_HASHTAG_LINE = re.compile(r'^\s*(#[\w-]+)(\s+#[\w-]+)+\s*$')

def escape_stray_hashtags(text):
    """Prevent trailing hashtag lines (e.g. '#coding #python') from being
    parsed as Markdown headings. Only touches lines that look like a pure
    tag list, so intentional '# Heading' usage is untouched."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if _HASHTAG_LINE.match(line):
            lines[i] = re.sub(r'#', r'\#', line)
    return '\n'.join(lines)

def utcnow():
    """Callable default for DateTime columns.
    Passed as a callable — not a value — so each row
    gets the time it was created, not the server start time.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio           = db.Column(db.String(300), default="")
    avatar_url    = db.Column(db.String(500), default="")
    is_admin      = db.Column(db.Boolean,     default=False)
    is_verified   = db.Column(db.Boolean,     default=False)
    joined_at     = db.Column(db.DateTime,    default=utcnow)

    # Modern bidirectional relationships
    posts    = db.relationship("Post",    back_populates="author", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="author", lazy="dynamic", cascade="all, delete-orphan")
    likes    = db.relationship("Like",    back_populates="user",   lazy="dynamic", cascade="all, delete-orphan")
    
    received_notifications = db.relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    sent_notifications     = db.relationship("Notification", foreign_keys="Notification.actor_id", back_populates="actor", lazy="dynamic", cascade="all, delete-orphan")

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

    def get_token(self, salt, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt=salt)

    @staticmethod
    def verify_token(token, salt, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt=salt, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return db.session.get(User, user_id)


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
    author_id  = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime,    default=utcnow)

    author   = db.relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")
    likes    = db.relationship("Like",    back_populates="post", cascade="all, delete-orphan", lazy="dynamic")
    views    = db.relationship("PostView", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def view_count(self):
        return self.views.count()

    @property
    def read_time(self):
        words   = len(self.content.split())
        minutes = max(1, round(words / 200))
        return f"{minutes} min read"

    @property
    def rendered_content(self):
        raw_html = markdown.markdown(
            escape_stray_hashtags(self.content),
            extensions=["fenced_code", "tables", "nl2br"]
        )
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
            'pre', 'code', 'br', 'hr', 
            'table', 'tr', 'td', 'th', 'tbody', 'thead',
            'img', 'span', 'div'
        ]
        allowed_attrs = {
            **bleach.sanitizer.ALLOWED_ATTRIBUTES,
            'img': ['src', 'alt', 'title'],
            'span': ['class'],
            'div': ['class'],
            'code': ['class']
        }
        return bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs)


class Like(db.Model):
    __tablename__ = "likes"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "post_id"),)

    user = db.relationship("User", back_populates="likes")
    post = db.relationship("Post", back_populates="likes")


class Comment(db.Model):
    __tablename__ = "comments"

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    parent_id  = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    author = db.relationship("User", back_populates="comments")
    post   = db.relationship("Post", back_populates="comments")

    # FIX: Configured to pull loaded arrays directly so Jinja truthiness evaluations work out-of-the-box
    parent  = db.relationship("Comment", remote_side=[id], back_populates="replies")
    replies = db.relationship("Comment", back_populates="parent", cascade="all, delete-orphan", lazy="select")

    
    @property
    def rendered_content(self):
        # Stricter than Post. No tables, no images in comments
        html = markdown.markdown(
            escape_stray_hashtags(self.content), 
            extensions=["nl2br"])
        allowed_tags = ['p', 'br', 'strong', 'em', 'code', 'a', 'ul', 'ol', 'li']
        allowed_attrs = {'a': ['href', 'rel', 'target']}
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)


class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)   # recipient
    actor_id   = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)   # trigger source
    notif_type = db.Column(db.String(30), nullable=False)                                               # "like", "comment", or "reply"
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    # FIX: Fully tracked bidirectional back-populations replacing legacy string backrefs
    user    = db.relationship("User", foreign_keys=[user_id], back_populates="received_notifications")
    actor   = db.relationship("User", foreign_keys=[actor_id], back_populates="sent_notifications")
    post    = db.relationship("Post")
    comment = db.relationship("Comment")


class PostView(db.Model):
    """
    Tracks unique post views for analytics.

    Privacy-first design:
    - Visitor IP is SHA-256 hashed before storage — the raw IP is never persisted.
    - One unique view per (post, ip_hash) per 24-hour window.
    - No user tracking for anonymous visitors — only a hash is stored.
    """
    __tablename__ = "post_views"

    id        = db.Column(db.Integer,     primary_key=True)
    post_id   = db.Column(db.Integer,     db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    ip_hash   = db.Column(db.String(64),  nullable=False)   # SHA-256 hex digest of visitor IP
    viewed_at = db.Column(db.DateTime,    default=utcnow)

    post = db.relationship("Post", back_populates="views")

    @staticmethod
    def hash_ip(ip: str) -> str:
        """Return a SHA-256 hex digest of the IP address for privacy-safe storage."""
        return hashlib.sha256(ip.encode()).hexdigest()
