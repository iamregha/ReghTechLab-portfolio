"""
user/routes.py
==============
Two user-facing routes:

  /user/dashboard  — Private. The logged-in user manages their profile
                     and sees all their posts (drafts + published).

  /user/<username> — Public. Anyone can visit a user's profile to read
                     their published posts and see their bio.
"""
import cloudinary
import cloudinary.uploader
from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from . import user_blueprint
from ..extensions import db
from ..models import User, Post, Notification

@user_blueprint.route("/notifications")
@login_required
def notifications():
    # Mark all as read when user opens inbox
    db.session.execute(
        db.update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    db.session.commit()

    # Get last 50 for full inbox page
    notifs = db.session.execute(
        db.select(Notification)
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).scalars().all()

    return render_template("user/notifications.html", notifications=notifs)


@user_blueprint.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """
    The user's personal control panel.

    GET  → Renders the dashboard with the user's posts and stats.
    POST → Handles the profile-update form (bio + avatar upload).

    WHY separate GET/POST in one route?
    This is called the PRG (Post-Redirect-Get) pattern.
    After a POST we always redirect so that refreshing the page
    won't accidentally re-submit the form.
    """
    if request.method == "POST":
        # ── Bio update ─────────────────────────────────────
        # Strip whitespace and enforce the 300-char limit from the model.
        bio = request.form.get("bio", "").strip()[:300]
        current_user.bio = bio

        # ── Avatar upload ──────────────────────────────────
        # request.files holds any <input type="file"> data from the form.
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            # Upload to Cloudinary. The folder kwarg organises uploads
            # cleanly in your Cloudinary media library.
            result = cloudinary.uploader.upload(
                avatar_file,
                folder="avatars",
                # Crop to a square and resize to 200px — keeps avatars consistent.
                transformation=[{"width": 200, "height": 200, "crop": "fill", "gravity": "face"}]
            )
            current_user.avatar_url = result.get("secure_url", "")

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user.dashboard"))

    # ── GET: gather data for the template ─────────────────
    # Fetch ALL posts (published AND drafts) for this user.
    # The dashboard is private, so the author can see their own drafts.
    all_posts = db.session.execute(
        db.select(Post)
        .filter_by(author_id=current_user.id)
        .order_by(Post.created_at.desc())
    ).scalars().all()

    # ── Stats: sum likes and comments across all posts ─────
    # These give the user a quick sense of their overall reach.
    total_likes    = sum(p.like_count    for p in all_posts)
    total_comments = sum(p.comment_count for p in all_posts)

    return render_template(
        "user/dashboard.html",
        posts=all_posts,
        total_likes=total_likes,
        total_comments=total_comments,
    )


@user_blueprint.route("/<username>")
def profile(username):
    """
    Public profile page for any user.

    We use 'first_or_404' here: if no user has this username,
    Flask automatically returns a 404 page — no manual check needed.
    This is clean and idiomatic Flask.
    """
    # Fetch the user or return a 404 automatically.
    # db.session.execute + scalar_one_or_none + manual abort is the
    # SQLAlchemy 2.0-style equivalent of the old User.query.filter_by().first_or_404()
    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()

    if user is None:
        abort(404)

    # Only fetch PUBLISHED posts for the public profile.
    # A visitor should never see someone's unpublished drafts.
    published_posts = db.session.execute(
        db.select(Post)
        .filter_by(author_id=user.id, published=True)
        .order_by(Post.created_at.desc())
    ).scalars().all()

    return render_template(
        "user/profile.html",
        profile_user=user,        # named 'profile_user' to avoid shadowing Flask's 'user' concept
        posts=published_posts,
    )
