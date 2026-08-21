from functools import wraps
from flask import render_template, current_app, redirect, url_for
import requests
from flask_login import current_user
import threading
import os

"""
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
"""

def send_email(to, subject, template, **kwargs):
    """HTTP email - works on Render free, no SMTP"""
    app = current_app._get_current_object()

    # dev intercept - same as yours
    if app.debug and not os.getenv('RESEND_API_KEY'):
        print(f"\n--- DEV EMAIL TO {to}: {subject} ---\n")
        return

    html = render_template(f"{template}.html", **kwargs)
    text_body = render_template(f"{template}.txt", **kwargs)

    def _send():
        with app.app_context():
            try:
                resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}"},
                    json={
                        "from": current_app.config['MAIL_DEFAULT_SENDER'],
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text_body
                    },
                    timeout=15
                )
                if resp.status_code!= 200:
                    current_app.logger.error(f"Resend error: {resp.text}")
            except Exception as e:
                current_app.logger.error(f"Failed to send email: {e}")

    import threading
    threading.Thread(target=_send, daemon=True).start()


def verified_required(f):
    """
    Decorator to ensure that the current_user has verified their email.
    Must be placed AFTER @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        
        if not current_user.is_verified and not current_app.config.get('TESTING'):
            return redirect(url_for('auth.unverified'))
            
        return f(*args, **kwargs)
    return decorated_function
