from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity
from functools import wraps
from flask import jsonify, request
import re

bcrypt = Bcrypt()

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(password_hash, password):
    """Check if password matches hash."""
    return bcrypt.check_password_hash(password_hash, password)

def generate_token(user_id):
    """Generate JWT access token."""
    return create_access_token(identity=user_id)

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength - relaxed for development."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Relaxed validation for development - just check length
    return True, "Password is valid"

def require_role(required_roles):
    """Decorator to check user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from models.database import User, db
            from flask_jwt_extended import jwt_required, get_jwt_identity
            
            # This will be called after jwt_required
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in required_roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_client_ip():
    """Get client IP address from request."""
    try:
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return request.environ['REMOTE_ADDR']
        else:
            return request.environ['HTTP_X_FORWARDED_FOR']
    except RuntimeError:
        # Working outside of request context (e.g., background tasks)
        return 'background-task'
