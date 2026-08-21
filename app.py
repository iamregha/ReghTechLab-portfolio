"""
app.py
======
Entry point. Creates and runs the application.
All logic lives in the portfolio/ package.
"""
from werkzeug.middleware.proxy_fix import ProxyFix
from portfolio import create_app

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
if __name__ == "__main__":
    app.run(debug=True)