#!/usr/bin/env python3
"""
Check users in the database
"""

import os
import sys
sys.path.append('backend')

from pymongo import MongoClient
from dotenv import load_dotenv

def check_users():
    """Check users in the MongoDB database."""
    
    print("👥 Checking Users in Database")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv('backend/.env')
    mongo_uri = os.getenv('MONGO_URI')
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client['radiological_detection']
        users_collection = db['users']
        
        # Count users
        user_count = users_collection.count_documents({})
        print(f"📊 Total users in database: {user_count}")
        
        if user_count > 0:
            print("\n👤 Users found:")
            users = users_collection.find({}, {"password_hash": 0})  # Exclude password hash
            for i, user in enumerate(users, 1):
                print(f"   {i}. Username: {user.get('username', 'N/A')}")
                print(f"      Email: {user.get('email', 'N/A')}")
                print(f"      Role: {user.get('role', 'N/A')}")
                print(f"      Active: {user.get('is_active', 'N/A')}")
                print(f"      Created: {user.get('created_at', 'N/A')}")
                print()
        else:
            print("\n❌ No users found in database!")
            print("💡 Creating admin user...")
            
            # Create admin user
            from werkzeug.security import generate_password_hash
            from datetime import datetime
            import uuid
            
            admin_user = {
                "_id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            result = users_collection.insert_one(admin_user)
            print(f"✅ Admin user created with ID: {result.inserted_id}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        return False

if __name__ == "__main__":
    check_users()
