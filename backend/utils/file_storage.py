#!/usr/bin/env python3
"""
Simple file-based storage system for when MongoDB is not available
"""
import json
import os
from datetime import datetime
import uuid

class FileStorage:
    """Simple file-based storage for user data."""
    
    def __init__(self, storage_dir="data"):
        self.storage_dir = storage_dir
        self.users_file = os.path.join(storage_dir, "users.json")
        self._ensure_storage_dir()
        self._load_users()
    
    def _ensure_storage_dir(self):
        """Create storage directory if it doesn't exist."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _load_users(self):
        """Load users from file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}
    
    def _save_users(self):
        """Save users to file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def create_user(self, username, email, password_hash, role='operator'):
        """Create a new user."""
        user_id = str(uuid.uuid4())
        user_data = {
            '_id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'is_active': True
        }
        
        self.users[user_id] = user_data
        self._save_users()
        
        # Return mock result like MongoDB
        class MockResult:
            def __init__(self, user_id):
                self.inserted_id = user_id
        
        return MockResult(user_id)
    
    def find_user_by_email(self, email):
        """Find user by email."""
        for user_id, user_data in self.users.items():
            if user_data.get('email') == email:
                return user_data
        return None
    
    def find_user_by_id(self, user_id):
        """Find user by ID."""
        return self.users.get(user_id)
    
    def update_last_login(self, user_id):
        """Update user's last login time."""
        if user_id in self.users:
            self.users[user_id]['last_login'] = datetime.utcnow().isoformat()
            self._save_users()
    
    def user_to_dict(self, user_doc):
        """Convert user document to dictionary."""
        if not user_doc:
            return None
        return {
            'id': user_doc['_id'],
            'username': user_doc['username'],
            'email': user_doc['email'],
            'role': user_doc['role'],
            'created_at': user_doc.get('created_at'),
            'last_login': user_doc.get('last_login'),
            'is_active': user_doc.get('is_active', True)
        }

# Global file storage instance
file_storage = FileStorage()
