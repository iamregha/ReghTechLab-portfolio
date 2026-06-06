"""
auth/routes.py
==============
Authentication blueprint and all auth routes.
Blueprint is defined here — not in __init__.py —
to keep all auth logic in one readable file.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from portfolio.extensions import db, limiter
from portfolio.models import User
from portfolio.utils import send_email

# Blueprint defined at module level
# 'auth' is the blueprint name used in url_for('auth.login')
auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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
            
            # Send verification email
            token = user.get_token(salt='email-verify')
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            send_email(user.email, "Verify Your Account - ReghTechLab", "email/verify_email", user=user, verify_url=verify_url)

            login_user(user)
            flash(f"Welcome to ReghTechLab, {username}! Please check your email to verify your account.", "success")
            return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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


@auth.route("/unverified")
@login_required
def unverified():
    if current_user.is_verified:
        return redirect(url_for("main.index"))
    return render_template("auth/unverified.html")


@auth.route("/resend_verification")
@login_required
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.is_verified:
        return redirect(url_for("main.index"))
    
    token = current_user.get_token(salt='email-verify')
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    send_email(current_user.email, "Verify Your Account - ReghTechLab", "email/verify_email", user=current_user, verify_url=verify_url)
    flash("A new verification email has been sent.", "info")
    return redirect(url_for("auth.unverified"))


@auth.route("/verify_email/<token>")
def verify_email(token):
    user = User.verify_token(token, salt='email-verify')
    if not user:
        flash("The verification link is invalid or has expired.", "error")
        return redirect(url_for("main.index"))
    
    if user.is_verified:
        flash("Account already verified. Please log in.", "info")
        return redirect(url_for("auth.login"))
        
    user.is_verified = True
    db.session.commit()
    flash("Your account has been verified! You can now publish posts.", "success")
    return redirect(url_for("main.index"))


@auth.route("/reset_password_request", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user:
            token = user.get_token(salt='password-reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_email(user.email, "Reset Your Password - ReghTechLab", "email/reset_password", user=user, reset_url=reset_url)
        
        # Always show success to prevent email enumeration
        flash("Check your email for the instructions to reset your password", "info")
        return redirect(url_for("auth.login"))
        
    return render_template("auth/reset_password_request.html")


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        
    user = User.verify_token(token, salt='password-reset')
    if not user:
        flash("That is an invalid or expired token", "error")
        return redirect(url_for("auth.reset_password_request"))
        
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Your password has been updated! You are now able to log in", "success")
            return redirect(url_for("auth.login"))
            
    return render_template("auth/reset_password.html", token=token)