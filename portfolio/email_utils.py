"""
portfolio/email_utils.py
========================
Async email helpers for Flask-Mail.

Why threading instead of Celery?
  At portfolio scale, a simple daemon thread is sufficient.
  Celery requires a Redis broker, a worker process, and extra Docker services.
  A thread achieves the same result (non-blocking request) with zero infra overhead.
  The thread is a daemon, so it will not keep the process alive if the app shuts down.
"""
import threading
from flask import current_app
from flask_mail import Message

from .extensions import mail


def _send_async(app, msg: Message) -> None:
    """Thread target: push the mail message inside the app context."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            # Log but do not crash - email failure should never break the app.
            app.logger.error("Email send failed: %s", exc)


def send_async_email(msg: Message) -> None:
    """
    Fire ``msg`` in a background daemon thread.

    The current app is captured before the thread starts so the
    application context is available inside the thread.
    """
    app = current_app._get_current_object()
    thread = threading.Thread(target=_send_async, args=(app, msg), daemon=True)
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

    msg = Message(
        subject  = f"[ReghTechLab Contact] {subject or 'No Subject'}",
        sender   = current_app.config["MAIL_DEFAULT_SENDER"],
        recipients = [contact_email],
        reply_to = email,
        body     = f"From: {name} <{email}>\n\n{message}",
    )
    send_async_email(msg)
