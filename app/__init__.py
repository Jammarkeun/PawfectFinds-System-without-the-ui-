from flask import Flask
from flask_session import Session
from flask_wtf import CSRFProtect
import os

# Initialize extensions
sess = Session()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    
    # Initialize extensions
    sess.init_app(app)
    csrf.init_app(app)
    
    # Create upload directories
    upload_folders = [
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'products'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'documents')
    ]
    
    for folder in upload_folders:
        os.makedirs(folder, exist_ok=True)
    
    # Register blueprints (only main for now)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.models import user
    
    return app
