from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.client import client_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(client_bp, url_prefix='/client')

    return app
