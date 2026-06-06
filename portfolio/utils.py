from functools import wraps
from flask import render_template, current_app, redirect, url_for
from flask_mail import Message
from flask_login import current_user
import threading

from .extensions import mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")

def send_email(to, subject, template, **kwargs):
    """
    Sends an email asynchronously so it doesn't block the request.
    If running locally without an SMTP server, it will print to console.
    """
    app = current_app._get_current_object()
    msg = Message(subject,
                  sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@reghtechlab.com'),
                  recipients=[to])
    
    msg.body = render_template(template + '.txt', **kwargs)
    try:
        msg.html = render_template(template + '.html', **kwargs)
    except Exception:
        pass

    # If no real mail configuration exists, just print to console for dev
    if app.debug and app.config.get('MAIL_SERVER') == 'localhost':
        print("\n" + "="*50)
        print(f"--- DEVELOPMENT EMAIL INTERCEPT ---")
        print(f"TO: {to}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{msg.body}")
        print("="*50 + "\n")
        return

    thr = threading.Thread(target=send_async_email, args=[app, msg])
    thr.start()


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
