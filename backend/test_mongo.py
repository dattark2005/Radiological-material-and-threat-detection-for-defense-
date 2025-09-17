#!/usr/bin/env python3
"""
Test MongoDB Atlas connection
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB Atlas connection."""
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv('MONGO_URI')
        print(f"🔗 Connecting to: {mongo_uri[:50]}...")
        
        # Create MongoDB client
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Get database
        db = client.get_database('radiological_detection')
        print(f"📊 Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        # Test insert
        test_collection = db.test_connection
        result = test_collection.insert_one({"test": "connection", "timestamp": "2025-09-17"})
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Testing MongoDB Atlas Connection...")
    print("=" * 50)
    success = test_mongodb_connection()
    print("=" * 50)
    if success:
        print("🎉 MongoDB Atlas is ready for your application!")
    else:
        print("⚠️  Please check your MongoDB Atlas configuration")
