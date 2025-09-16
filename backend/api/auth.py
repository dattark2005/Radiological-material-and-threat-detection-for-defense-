from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models.database import User
from utils.auth import hash_password, check_password, generate_token, validate_email, validate_password
from utils.logger import log_system_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        role = data.get('role', 'operator')
        
        # Validate input
        if len(username) < 3:
            return jsonify({'message': 'Username must be at least 3 characters long'}), 400
        
        if not validate_email(email):
            return jsonify({'message': 'Invalid email format'}), 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Check if user already exists
        if User.find_by_email(email):
            return jsonify({'message': 'Email already registered'}), 409
        
        # Create new user
        result = User.create(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role
        )
        
        user_id = result.inserted_id
        
        log_system_event('INFO', f'New user registered: {username}', 'auth', str(user_id))
        
        # Get the created user
        user_doc = User.find_by_email(email)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': User.to_dict(user_doc)
        }), 201
        
    except Exception as e:
        log_system_event('ERROR', f'Registration error: {str(e)}', 'auth')
        return jsonify({'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    try:
        data = request.get_json()
        
        if 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user by email (treating username as email for simplicity)
        user_doc = User.find_by_email(username)
        
        if not user_doc or not check_password(user_doc['password_hash'], password):
            log_system_event('WARNING', f'Failed login attempt for: {username}', 'auth')
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user_doc.get('is_active', True):
            return jsonify({'message': 'Account is deactivated'}), 401
        
        # Update last login
        User.update_last_login(user_doc['_id'])
        
        # Generate token
        token = generate_token(user_doc['_id'])
        
        log_system_event('INFO', f'User logged in: {username}', 'auth', user_doc['_id'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': User.to_dict(user_doc)
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Login error: {str(e)}', 'auth')
        return jsonify({'message': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)."""
    try:
        user_id = get_jwt_identity()
        user_doc = User.find_by_id(user_id)
        
        if user_doc:
            log_system_event('INFO', f'User logged out: {user_doc["username"]}', 'auth', user_doc['_id'])
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Logout error: {str(e)}', 'auth')
        return jsonify({'message': 'Logout failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    try:
        user_id = get_jwt_identity()
        user_doc = User.find_by_id(user_id)
        
        if not user_doc:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({'user': User.to_dict(user_doc)}), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Profile fetch error: {str(e)}', 'auth')
        return jsonify({'message': 'Failed to fetch profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                return jsonify({'message': 'Invalid email format'}), 400
            
            # Check if email is already taken by another user
            existing_user = User.find_by_email(email)
            
            if existing_user and existing_user['_id'] != user_doc['_id']:
                return jsonify({'message': 'Email already registered'}), 409
        
        # Update user document
        update_data = {}
        if 'email' in data:
            update_data['email'] = email
        if 'password' in data:
            password = data['password']
            is_valid, message = validate_password(password)
            if not is_valid:
                return jsonify({'message': message}), 400
            update_data['password_hash'] = hash_password(password)
        
        if update_data:
            from models.database import mongo
            mongo.db.users.update_one(
                {'_id': user_doc['_id']},
                {'$set': update_data}
            )
        
        log_system_event('INFO', f'Profile updated: {user_doc["username"]}', 'auth', user_doc['_id'])
        
        # Get updated user
        updated_user = User.find_by_id(user_doc['_id'])
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': User.to_dict(updated_user)
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Profile update error: {str(e)}', 'auth')
        return jsonify({'message': 'Failed to update profile'}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users (admin only)."""
    try:
        from utils.auth import role_required
        
        # Check if user has admin role
        user_id = get_jwt_identity()
        current_user = User.find_by_id(user_id)
        
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        from models.database import mongo
        users = list(mongo.db.users.find())
        return jsonify({
            'users': [User.to_dict(user) for user in users]
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'User list error: {str(e)}', 'auth')
        return jsonify({'message': 'Failed to fetch users'}), 500
