import sys
from pathlib import Path

from flask import Flask


# Allow `python backend/app.py` to resolve `backend.*` imports by ensuring
# the project root is on sys.path when this file is executed directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.routes.user_routes import user_bp
from backend.routes.chat_routes import chat_bp
from backend.routes.meal_routes import meal_bp
from backend.routes.nutrition_routes import nutrition_bp

def create_app():
    """
    Factory function that creates and configures the Flask app.
    Using a factory function (instead of a global app object) makes
    testing easier — you can create a fresh app for each test.
    """
    app = Flask(__name__)

    # Register blueprints — each blueprint owns a URL prefix.
    # user_bp handles everything under /api/user/
    # chat_bp handles everything under /api/chat/
    # meal_bp handles everything under /api/meal/
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(meal_bp, url_prefix="/api/meal")
    app.register_blueprint(nutrition_bp, url_prefix="/api/nutrition")

    return app


if __name__ == "__main__":
    app = create_app()
    # debug=True means Flask auto-restarts when you edit a file
    # and shows detailed error pages — only use in development
    app.run(debug=True, port=5000)
