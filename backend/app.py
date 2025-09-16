from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import os
import logging
from datetime import datetime

from config.config import config
from models.database import mongo
from utils.logger import setup_logging
from utils.auth import bcrypt

# Import blueprints
from api.auth import auth_bp
from api.dashboard import dashboard_bp
from api.upload import upload_bp
from api.analysis import analysis_bp
from api.threats import threats_bp
from api.reports import reports_bp
from api.isotopes import isotopes_bp
from api.logs import logs_bp
from api.monitoring import monitoring_bp

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])
    
    # Setup logging
    setup_logging(app)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(threats_bp, url_prefix='/api/threats')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(isotopes_bp, url_prefix='/api/isotopes')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
    
    # Initialize MongoDB collections and data
    with app.app_context():
        # Initialize isotope database if empty
        from models.database import init_isotope_database
        init_isotope_database()
        
        # Create admin user if not exists
        from models.database import User
        from utils.auth import hash_password
        admin_user = User.find_by_email(app.config.get('ADMIN_EMAIL', 'admin@example.com'))
        if not admin_user:
            User.create(
                username=app.config.get('ADMIN_USERNAME', 'admin'),
                email=app.config.get('ADMIN_EMAIL', 'admin@example.com'),
                password_hash=hash_password(app.config.get('ADMIN_PASSWORD', 'admin123')),
                role='admin'
            )
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    
    # WebSocket events
    from services.websocket_service import register_socketio_events
    register_socketio_events(socketio)
    
    app.socketio = socketio
    return app

if __name__ == '__main__':
    app = create_app()
    app.socketio.run(app, debug=True, host='0.0.0.0', port=5000)
