"""
ReghTechLab Portfolio
=====================
Author  : Abraham Regha
Stack   : Flask + SQLAlchemy + Flask-Login + Jinja2 + Tailwind CSS
"""

import os
import sys
from datetime import datetime, timezone
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify
from flask_wtf import CSRFProtect

# Load environment variables from .env
load_dotenv()

# Flask application instance
app = Flask(__name__)

# Configuation
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-fallback-change-this")

# Dynamic DB logic (Postgres on Railway, SQLite locally)
if "pytest" in sys.modules:
    db_url = "sqlite:///:memory:"
else:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# CSRF Protection
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask-Login setup
login_manager = LoginManager(app)

# redirect unauthenticated users
login_manager.login_view = "login"


# Datbase Models
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), default="")
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default= lambda:datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_liked(self, post):
        return db.session.execute(
            db.select(Like).filter_by(
                user_id=self.id, 
                post_id=post.id)
        ).scalar_one_or_none() is not None

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
    cover_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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

    @property
    def rendered_content(self):
        import markdown
        return markdown.markdown(
            self.content,
            extensions=["fenced_code", "tables", "nl2br"]
    )

    
class Comment(db.Model):
    __tablename__ = "comments"

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"),  nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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

# to reload user from session
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes

@app.route("/")
def index():
    """Homepage - the portfolio landing page"""
    return render_template("index.html")


@app.route("/about")
def about():
    """About page - explains the ReghtechLab mission."""
    return render_template("about.html")

@app.route("/contact")
def contact():
    """Contact page - let's start a conversation."""
    return render_template("contact.html")


# Auth Routes

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # confirm no error anywhere before touching the database
        error = None
        
        if not all([username, email, password, confirm]):
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be atleast 3 characters."
        elif password != confirm:
            error = "Passsword do not match."
        elif len(password) < 8:
            error ="Password must be at least 8 characters."
        elif db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none():
            error = "Username already taken."
        elif db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none():
            error = "Email already registered."

        if error:
            flash(error, "error")
        else:
            # ── Create the user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # ── Log them in immediately after registering
            login_user(user)
            flash(f"Welcome to ReghTechLab, {username}!", "success")
            return redirect(url_for("index"))

    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = bool(request.form.get("remember"))

        # Allow login with either username OR email
        user = db.session.execute(
            db.select(User).filter_by(email=identifier)
        ).scalar_one_or_none()

        if not user:
            user = db.session.execute(
                db.select(User).filter_by(username=identifier)
            ).scalar_one_or_none()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")

            # Redirect to the page they were trying to visit
            # before being sent to login
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# Blog Routes
@app.route("/blog")
def blog():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()

    query = db.select(Post).filter_by(published=True)

    if category:
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            db.or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%"),
                Post.excerpt.ilike(f"%{search}%"),
            )
        )

    posts = db.paginate(
        query, page=page, per_page=6, error_out=False
    )

    categories = [
        "Python & Backend",
        "Industrial Automation",
        "Retail Operations",
        "IoT & Embedded",
        "Maintenance & Reliability",
        "Tutorials",
    ]   

    return render_template(
        "blog/index.html",
        posts=posts,
        categories=categories,
        active_category=category,
        search=search,
    )

@app.route("/blog/new", methods=["GET", "POST"])
@login_required
def new_post():
    categories = [
        "Python & Backend",
        "Industrial Automation",
        "Retail Operations",
        "IoT & Embedded",
        "Maintenance & Reliability",
        "Tutorials",
    ]  
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        excerpt = request.form.get("excerpt", "").strip()
        category = request.form.get("category", "").strip()
        published = bool(request.form.get("published"))

        error = None

        if not all([title, content, excerpt, category]):
            error = "All fields are required."
        elif len(title) < 5:
            error = "Title must be at least 5 characters."
        elif len(content) < 50:
            error = "Content must be at least 50 characters."
        elif len(excerpt) < 10:
            error = "Excerpt must be at least 10 characters."
        elif len(category) < 3:
            error = "Category must be at least 3 characters."

        if error:
            flash(error, "error")
        else:
            base_slug = slugify(title)
            unique_slug = base_slug
            counter = 1
            while db.session.execute(
                db.select(Post).filter_by(slug=unique_slug)
            ).scalar_one_or_none() is not None:
                unique_slug = f"{base_slug}-{counter}"
                counter += 1    
            
            # Handle Image Upload to Cloudinary
            cover_url = request.form.get("existing_cover_url", "").strip()
            cover_image = request.files.get("cover_image")
            if cover_image and cover_image.filename:
                # Returns dictionary with info, including secure_url
                upload_result = cloudinary.uploader.upload(cover_image)
                cover_url = upload_result.get("secure_url", cover_url)

            post = Post(
                title=title,
                slug=unique_slug,
                content=content,
                excerpt=excerpt,
                category=category,
                cover_url=cover_url,
                published=published,
                author_id=current_user.id,
            )
            db.session.add(post)
            db.session.commit()
            flash("Post created successfully!", "success")
            return redirect(url_for("blog"))

    return render_template("blog/new_post.html", categories=categories)

@app.route("/blog/<slug>", methods=["GET", "POST"])
def blog_post(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug, published=True)
    ).scalar_one_or_none()

    if not post:
        abort(404)

    # Handle comment submission
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Log in to post a comment.", "info")
            return redirect(url_for("login"))

        content = request.form.get("content", "").strip()

        if not content:
            flash("Comment cannot be empty.", "error")
        elif len(content) > 2000:
            flash("Comment too long.", "error")
        else:
            comment = Comment(
                content   = content,
                author_id = current_user.id,
                post_id   = post.id,
            )
            db.session.add(comment)
            db.session.commit()
            flash("Comment posted.", "success")

        return redirect(
            url_for("blog_post", slug=slug) + "#comments"
        )

    comments = db.session.execute(
        db.select(Comment)
        .filter_by(post_id=post.id)
        .order_by(Comment.created_at.asc())
    ).scalars().all()

    related = db.session.execute(
        db.select(Post).filter(
            Post.category == post.category,
            Post.id != post.id,
            Post.published == True
        )
        .order_by(Post.created_at.desc())
        .limit(3)
    ).scalars().all()

    return render_template(
        "blog/post.html",
        post=post,
        comments=comments,
        related=related,
    )


@app.route("/blog/<slug>/like", methods=["POST"])
@login_required
@csrf.exempt
def toggle_like(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug)
    ).scalar_one_or_none()

    if not post:
        abort(404)

    existing = db.session.execute(
        db.select(Like).filter_by(
            user_id=current_user.id,
            post_id=post.id
        )
    ).scalar_one_or_none()

    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(
            user_id=current_user.id,
            post_id=post.id
        ))
        liked = True

    db.session.commit()
    return jsonify({"liked": liked, "count": post.like_count})

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)

    if not comment:
        abort(404)

    if comment.author_id != current_user.id:
        abort(403)

    slug = comment.post.slug
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "info")
    return redirect(
        url_for("blog_post", slug=slug) + "#comments"
    ) 


@app.route("/blog/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_post(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug)
    ).scalar_one_or_none()

    if not post:
        abort(404)

    if post.author_id != current_user.id:
        abort(403)

    categories = [
        "Python & Backend",
        "Industrial Automation",
        "Retail Operations",
        "IoT & Embedded",
        "Maintenance & Reliability",
        "Tutorials",
    ]

    if request.method == "POST":
        post.title     = request.form.get("title","").strip()
        post.excerpt   = request.form.get("excerpt","").strip()
        post.content   = request.form.get("content","").strip()
        post.category  = request.form.get("category", post.category)
        
        # Cloudinary logic + fallback url
        cover_url = request.form.get("existing_cover_url", "").strip()
        cover_image = request.files.get("cover_image")
        
        if cover_image and cover_image.filename:
            upload_result = cloudinary.uploader.upload(cover_image)
            cover_url = upload_result.get("secure_url", cover_url)
            
        if cover_url:
            post.cover_url = cover_url

        post.published = request.form.get("published") == "on"
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("blog_post", slug=post.slug))

    return render_template(
        "blog/new_post.html",
        post=post,
        categories=categories,
        editing=True
    )


@app.route("/blog/<slug>/delete", methods=["POST"])
@login_required
def delete_post(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug)
    ).scalar_one_or_none()

    if not post:
        abort(404)

    if post.author_id != current_user.id:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("blog"))



#with app.app_context():
#    db.create_all()

if "pytest" not in sys.modules:
    with app.app_context():
        from flask_migrate import upgrade as flask_upgrade
        flask_upgrade()

# Entry point
if __name__ == "__main__":
    app.run(debug=True)
