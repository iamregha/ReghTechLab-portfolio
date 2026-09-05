from functools import wraps
from flask import render_template, current_app, redirect, url_for
import requests
from flask_login import current_user
import threading
import os
from PIL import Image, UnidentifiedImageError

"""
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
"""

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_image_upload(file_storage) -> tuple[bool, str]:
    """
    Validate an uploaded image before it's sent to Cloudinary.

    Checks:
      1. File extension is in the allowed list (cheap first filter)
      2. Actual file size doesn't exceed the limit
      3. File content is genuinely a decodable image — Pillow
         attempts to actually open and verify the file's internal
         structure, not just its filename. A renamed .exe or
         corrupted file fails this check even with a valid-looking
         extension, because Pillow can't decode it as an image.

    Returns (is_valid, error_message). error_message is empty
    string if is_valid is True.
    """
    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, "Unsupported file type. Use JPG, PNG, GIF, or WEBP."

    # Check size — seek to end, read position, then reset
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)  # reset before Pillow reads it

    if size > MAX_IMAGE_SIZE_BYTES:
        return False, "Image too large. Maximum size is 5MB."

    # Verify actual image content using Pillow's decoder.
    # Image.verify() checks structural integrity without fully
    # decoding pixel data — fast, and catches corrupted or
    # non-image files disguised with a valid extension.
    try:
        img = Image.open(file_storage.stream)
        img.verify()
    except (UnidentifiedImageError, OSError):
        return False, "File content does not match a valid image format."
    finally:
        file_storage.stream.seek(0)  # reset for the actual Cloudinary upload

    return True, ""

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
