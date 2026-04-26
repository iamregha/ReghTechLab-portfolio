"""
blog/routes.py
==============
All blog routes: index, post view, new/edit/delete,
likes, and comment deletion.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
import cloudinary
import cloudinary.uploader
from flask_login import login_required, current_user
# from flask_wtf.csrf import csrf_exempt
from slugify import slugify

# from . import blog
from ..extensions import db
from ..models import Post, Comment, Like

blog = Blueprint("blog", __name__)

CATEGORIES = [
    "Python & Backend",
    "Industrial Automation",
    "Retail Operations",
    "IoT & Embedded",
    "Maintenance & Reliability",
    "Tutorials",
]


@blog.route("/blog")
def index():
    page     = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    search   = request.args.get("q", "").strip()

    query = db.select(Post).filter_by(published=True)

    if category:
        query = query.filter(Post.category == category)

    if search:
        query = query.filter(
            db.or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%"),
                Post.excerpt.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(Post.created_at.desc())
    posts = db.paginate(query, page=page, per_page=6, error_out=False)

    return render_template(
        "blog/index.html",
        posts=posts,
        categories=CATEGORIES,
        active_category=category,
        search=search,
    )


@blog.route("/blog/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title     = request.form.get("title", "").strip()
        content   = request.form.get("content", "").strip()
        excerpt   = request.form.get("excerpt", "").strip()
        category  = request.form.get("category", "").strip()
        published = bool(request.form.get("published"))

        error = None
        if not all([title, content, excerpt, category]):
            error = "All fields are required."
        elif len(title) < 5:
            error = "Title must be at least 5 characters."
        elif len(content) < 50:
            error = "Content must be at least 50 characters."

        if error:
            flash(error, "error")
        else:
            base_slug   = slugify(title)
            unique_slug = base_slug
            counter     = 1
            while db.session.execute(
                db.select(Post).filter_by(slug=unique_slug)
            ).scalar_one_or_none():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1

            cover_url   = request.form.get("existing_cover_url", "").strip()
            cover_image = request.files.get("cover_image")
            if cover_image and cover_image.filename:
                result    = cloudinary.uploader.upload(cover_image)
                cover_url = result.get("secure_url", cover_url)

            post = Post(
                title     = title,
                slug      = unique_slug,
                content   = content,
                excerpt   = excerpt,
                category  = category,
                cover_url = cover_url,
                published = published,
                author_id = current_user.id,
            )
            db.session.add(post)
            db.session.commit()
            flash("Post published.", "success")
            return redirect(url_for("blog.post", slug=post.slug))

    return render_template("blog/new_post.html", categories=CATEGORIES)


@blog.route("/blog/<slug>", methods=["GET", "POST"])
def post(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug, published=True)
    ).scalar_one_or_none()

    if not post:
        abort(404)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Log in to post a comment.", "info")
            return redirect(url_for("auth.login"))

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

        return redirect(url_for("blog.post", slug=slug) + "#comments")

    comments = db.session.execute(
        db.select(Comment)
        .filter_by(post_id=post.id)
        .order_by(Comment.created_at.asc())
    ).scalars().all()

    related = db.session.execute(
        db.select(Post).filter(
            Post.category == post.category,
            Post.id       != post.id,
            Post.published == True,
        )
        .order_by(Post.created_at.desc())
        .limit(3)
    ).scalars().all()

    return render_template(
        "blog/post.html",
        post=post, comments=comments, related=related,
    )


@blog.route("/blog/<slug>/like", methods=["POST"])
@login_required
#@csrf_exempt
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
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
        liked = True

    db.session.commit()
    return jsonify({"liked": liked, "count": post.like_count})


@blog.route("/blog/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_post(slug):
    post = db.session.execute(
        db.select(Post).filter_by(slug=slug)
    ).scalar_one_or_none()

    if not post:
        abort(404)
    if post.author_id != current_user.id:
        abort(403)

    if request.method == "POST":
        post.title    = request.form.get("title",    "").strip()
        post.excerpt  = request.form.get("excerpt",  "").strip()
        post.content  = request.form.get("content",  "").strip()
        post.category = request.form.get("category", post.category)
        post.published = request.form.get("published") == "on"

        cover_url   = request.form.get("existing_cover_url", "").strip()
        cover_image = request.files.get("cover_image")
        if cover_image and cover_image.filename:
            result    = cloudinary.uploader.upload(cover_image)
            cover_url = result.get("secure_url", cover_url)
        if cover_url:
            post.cover_url = cover_url

        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("blog.post", slug=post.slug))

    return render_template(
        "blog/new_post.html",
        post=post, categories=CATEGORIES, editing=True
    )


@blog.route("/blog/<slug>/delete", methods=["POST"])
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
    return redirect(url_for("blog.index"))


@blog.route("/comment/<int:comment_id>/delete", methods=["POST"])
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
    return redirect(url_for("blog.post", slug=slug) + "#comments")