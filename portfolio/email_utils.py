"""
portfolio/email_utils.py
========================
Async email helpers.

Why Resend instead of Flask-Mail/SMTP?
  Render's free tier blocks outbound SMTP ports (25, 465, 587)
  entirely — this is a platform-level restriction, not something
  fixable in application code. Resend uses HTTPS, which is never
  blocked, and is the standard approach for transactional email
  on modern free-tier hosts (Render, Vercel, etc.).
"""
import threading
import resend
from flask import current_app, render_template
# from flask_mail import Message

# from .extensions import mail


def _send_async(app, params: dict) -> None:
    """Thread target: push the mail message inside the app context."""
    with app.app_context():
        try:
            resend.Emails.send(params)
        except Exception as exc:
            # Log but do not crash - email failure should never break the app.
            app.logger.error("Email send failed: %s", exc)

def send_email(to: str, subject: str, template: str, **context) -> None:
    """
    Render an HTML email template and send it asynchronously via Resend.

    Args:
        to:       Recipient email address.
        subject:  Email subject line.
        template: Template path under templates/, WITHOUT extension.
                  Expects {{ template }}.html to exist.
                  e.g. "email/verify_email" resolves to
                  templates/email/verify_email.html
        **context: Any variables the template needs (user=user, etc).
    """
    app = current_app._get_current_object()
    resend.api_key = app.config["RESEND_API_KEY"]

    # Render the HTML body now, while we still have the real
    # request/app context — rendering inside the thread would
    # require re-establishing template context manually.
    html_body = render_template(f"{template}.html", **context)

    params = {
        "from":    app.config["MAIL_DEFAULT_SENDER"],
        "to":      [to],
        "subject": subject,
        "html":    html_body,
    }

    thread = threading.Thread(
        target=_send_async, args=(app, params), daemon=True
    )
    thread.start()


def send_async_email(params: dict) -> None:
    """
    
    """
    app = current_app._get_current_object()
    resend.api_key = app.config["RESEND_API_KEY"]
    thread = threading.Thread(target=_send_async, args=(app, params), daemon=True)
    thread.start()


def send_contact_email(name: str, email: str, subject: str, message: str) -> None:
    """
    Compose and asynchronously send a contact-form email to the site owner.

    Args:
        name:     Sender's full name.
        email:    Sender's email address (used as reply-to).
        subject:  Message subject line.
        message:  Body of the message.
    """
    contact_email = current_app.config.get("CONTACT_EMAIL", "noreply@reghtechlab.com")

    params = {
        "from": current_app.config["MAIL_DEFAULT_SENDER"],
        "to": [contact_email],
        "reply_to": email,
        "subject": f"[ReghTechLab Contact] {subject or 'No Subject'}",
        "text": f"From: {name} <{email}>\n\n{message}",
    }
    send_async_email(params)
