# Authentication System

The application uses **Flask-Login** to handle user sessions and authentication. 

## Features

- **Registration:** Users can sign up with a unique username, email, and password.
- **Flexible Login:** Users can log in using either their `username` or `email` address.
- **Password Hashing:** Passwords are securely hashed using `werkzeug.security` (`generate_password_hash` and `check_password_hash`) before being stored in the database.
- **Session Management:** Robust session handling out-of-the-box thanks to Flask-Login (`login_user`, `logout_user`, `login_required`).

## Security Built-in

- No plain-text passwords are ever stored.
- Secure fallback defaults are provided for the `SECRET_KEY` required by Flask for signing session cookies.
