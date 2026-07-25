"""
app.py
======
Entry point. Creates and runs the application.
All logic lives in the portfolio/ package.
"""
from portfolio import create_app
from portfolio.extensions import db

app = create_app()

# Safety net for Render free tier only - won't delete data
# If posts table is missing on first boot, create it
with app.app_context():
    try:
        from sqlalchemy import inspect
        import portfolio.models  # registers all models with db.metadata
        
        inspector = inspect(db.engine)
        if not inspector.has_table("posts"):
            print(">>> posts table missing, running create_all()")
            db.create_all()
    except Exception as e:
        print(f">>> DB check skipped: {e}")

if __name__ == "__main__":
    app.run(debug=True)