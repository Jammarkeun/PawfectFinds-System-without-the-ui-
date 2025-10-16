from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
import os

# Local application imports
from app.models.user import User
from app.services.database import Database
from config.config import Config
from app.controllers.auth_controller import auth_bp
from app.controllers.admin_controller import admin_bp
from app.controllers.seller_controller import seller_bp
from app.controllers.user_controller import user_bp
from app.controllers.public_controller import public_bp
from app.controllers.cart_controller import cart_bp
from app.controllers.order_controller import order_bp
from app.controllers.search_controller import search_bp
from app.controllers.review_controller import review_bp
from app.controllers.rider_controller import rider_bp

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    app.config.from_object(Config)

    # Initialize extensions
    csrf = CSRFProtect(app)
    db = Database()
    db.init_app(app)  # Add this line

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(seller_bp, url_prefix='/seller')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(public_bp, url_prefix='/')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(review_bp, url_prefix='/review')
    app.register_blueprint(rider_bp, url_prefix='/rider')

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.error(f"CSRF error: {e.description}")
        app.logger.error(f"Request method: {request.method}")
        app.logger.error(f"Request path: {request.path}")
        app.logger.error(f"Request form data: {dict(request.form)}")
        app.logger.error(f"Request cookies: {request.cookies}")
        app.logger.error(f"Session contents: {dict(session)}")
        flash('Your session expired or the form is invalid. Please try again.', 'error')
        return render_template('errors/403.html'), 403

    @app.before_request
    def create_tables():
        """Create database tables if they don't exist"""
        db.create_tables()

    @app.context_processor
    def inject_user():
        """Inject current user into all templates"""
        if 'user_id' in session:
            user = User.get_by_id(session['user_id'])
            return dict(current_user=user, csrf_token_value=generate_csrf())
        return dict(current_user=None, csrf_token_value=generate_csrf())

    @app.route('/')
    def index():
        """Main landing page"""
        return redirect(url_for('public.landing'))

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
