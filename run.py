"""
Application Entry Point
========================
Run with:
    python run.py

Or with gunicorn:
    gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
"""

from app import create_app
from app.extensions import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Tables created")
    app.run(debug=True, port=5000)
