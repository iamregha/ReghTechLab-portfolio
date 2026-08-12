"""
app.py
======
Entry point. Creates and runs the application.
All logic lives in the portfolio/ package.
"""
from portfolio import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)