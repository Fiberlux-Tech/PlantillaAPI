from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Import the api blueprint from your routes file
    from .routes import api as api_blueprint
    # Register the blueprint and set its URL prefix
    app.register_blueprint(api_blueprint, url_prefix='/api')

    with app.app_context():
        from . import models

    return app