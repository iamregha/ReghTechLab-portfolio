"""
auth/routes.py
==============
Authentication blueprint and all auth routes.
Blueprint is defined here — not in __init__.py —
to keep all auth logic in one readable file.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from portfolio.extensions import db
from portfolio.models import User

# Blueprint defined at module level
# 'auth' is the blueprint name used in url_for('auth.login')
auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        error = None
        if not all([username, email, password, confirm]):
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
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
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Welcome to ReghTechLab, {username}!", "success")
            return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = bool(request.form.get("remember"))

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
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))