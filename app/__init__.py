from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Application factory function. Creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure CORS to allow requests from the frontend
    CORS(app)

    # Register the API routes with the application
    with app.app_context():
        from . import routes
        from . import models

    return app