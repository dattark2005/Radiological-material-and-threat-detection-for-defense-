#!/usr/bin/env python3
"""
Migrate users from file storage to MongoDB Atlas
"""
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

def migrate_users():
    """Migrate users from file storage to MongoDB."""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGO_URI')
        print(f"🔗 Connecting to MongoDB...")
        client = MongoClient(mongo_uri)
        db = client.get_database('radiological_detection')
        users_collection = db.users
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Load users from file storage
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            print("❌ No users.json file found")
            return
        
        with open(users_file, 'r') as f:
            file_users = json.load(f)
        
        print(f"📁 Found {len(file_users)} users in file storage")
        
        # Migrate each user
        migrated_count = 0
        for user_id, user_data in file_users.items():
            # Check if user already exists in MongoDB
            existing_user = users_collection.find_one({'email': user_data['email']})
            
            if existing_user:
                print(f"⚠️  User {user_data['email']} already exists in MongoDB, skipping...")
                continue
            
            # Convert string dates back to datetime objects for MongoDB
            if isinstance(user_data.get('created_at'), str):
                try:
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                except:
                    user_data['created_at'] = datetime.utcnow()
            
            if isinstance(user_data.get('last_login'), str):
                try:
                    user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                except:
                    user_data['last_login'] = None
            elif user_data.get('last_login') is None:
                user_data['last_login'] = None
            
            # Insert user into MongoDB
            result = users_collection.insert_one(user_data)
            print(f"✅ Migrated user: {user_data['email']} -> {result.inserted_id}")
            migrated_count += 1
        
        print(f"\n🎉 Migration completed!")
        print(f"📊 Total users migrated: {migrated_count}")
        
        # Verify migration
        total_mongo_users = users_collection.count_documents({})
        print(f"📊 Total users in MongoDB: {total_mongo_users}")
        
        # List all users in MongoDB
        print("\n👥 Users in MongoDB:")
        for user in users_collection.find():
            print(f"  - {user['email']} ({user['role']}) - ID: {user['_id']}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting User Migration to MongoDB Atlas...")
    print("=" * 60)
    success = migrate_users()
    print("=" * 60)
    if success:
        print("✅ Migration completed successfully!")
        print("💡 You can now restart your Flask app to use MongoDB for new users")
    else:
        print("❌ Migration failed. Please check the errors above.")
