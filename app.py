"""
app.py
======
Entry point. Creates and runs the application.
All logic lives in the portfolio/ package.
"""
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_compress import Compress
from whitenoise import WhiteNoise
from portfolio import create_app

app = create_app()
Compress(app)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.template_filter('cld')
def cld_optimized(url, width=800):
    if url and 'cloudinary.com' in url and '/upload/' in url:
        return url.replace('/upload/', f'/upload/f_auto,q_auto,w_{width},c_limit/')
    return url

if __name__ == "__main__":
    app.run(debug=True)