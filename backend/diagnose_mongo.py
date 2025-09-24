#!/usr/bin/env python3
"""
MongoDB Atlas Connection Diagnostics
This script helps diagnose common MongoDB Atlas connection issues
"""
import os
import urllib.parse
from dotenv import load_dotenv
from pymongo import MongoClient
import requests

# Load environment variables
load_dotenv()

def parse_mongo_uri(uri):
    """Parse MongoDB URI to extract components."""
    print("🔍 Parsing MongoDB URI...")
    try:
        # Extract basic components
        if uri.startswith('mongodb+srv://'):
            protocol = 'mongodb+srv://'
            remainder = uri[14:]  # Remove mongodb+srv://
        elif uri.startswith('mongodb://'):
            protocol = 'mongodb://'
            remainder = uri[10:]  # Remove mongodb://
        else:
            print("❌ Invalid MongoDB URI format")
            return None
        
        # Split credentials and host
        if '@' in remainder:
            credentials, host_db = remainder.split('@', 1)
            if ':' in credentials:
                username, password = credentials.split(':', 1)
                # URL decode the password
                decoded_password = urllib.parse.unquote(password)
                print(f"👤 Username: {username}")
                print(f"🔑 Password: {'*' * len(decoded_password)} (length: {len(decoded_password)})")
                print(f"🔑 Raw Password: {password}")
                print(f"🔑 Decoded Password: {decoded_password}")
            else:
                print("❌ No password found in URI")
                return None
        else:
            print("❌ No credentials found in URI")
            return None
        
        # Extract host and database
        if '/' in host_db:
            host, database = host_db.split('/', 1)
            # Remove query parameters if any
            if '?' in database:
                database = database.split('?')[0]
        else:
            host = host_db
            database = None
        
        print(f"🌐 Host: {host}")
        print(f"🗄️  Database: {database}")
        
        return {
            'protocol': protocol,
            'username': username,
            'password': password,
            'decoded_password': decoded_password,
            'host': host,
            'database': database
        }
        
    except Exception as e:
        print(f"❌ Error parsing URI: {e}")
        return None

def test_network_connectivity():
    """Test basic network connectivity to MongoDB Atlas."""
    print("\n🌐 Testing Network Connectivity...")
    try:
        # Test DNS resolution and basic connectivity
        response = requests.get('https://cloud.mongodb.com', timeout=10)
        print("✅ Can reach MongoDB Atlas servers")
        return True
    except requests.RequestException as e:
        print(f"❌ Network connectivity issue: {e}")
        return False

def test_different_auth_methods(uri_components):
    """Test different authentication methods."""
    print("\n🔐 Testing Different Authentication Methods...")
    
    if not uri_components:
        print("❌ Cannot test - URI parsing failed")
        return False
    
    # Method 1: Original URI
    print("\n1️⃣ Testing with original URI...")
    original_uri = os.getenv('MONGO_URI')
    test_connection_method(original_uri, "Original URI")
    
    # Method 2: Re-encoded password
    print("\n2️⃣ Testing with re-encoded password...")
    encoded_password = urllib.parse.quote_plus(uri_components['decoded_password'])
    new_uri = f"{uri_components['protocol']}{uri_components['username']}:{encoded_password}@{uri_components['host']}/{uri_components['database']}"
    test_connection_method(new_uri, "Re-encoded password")
    
    # Method 3: Without database name
    print("\n3️⃣ Testing without specific database...")
    no_db_uri = f"{uri_components['protocol']}{uri_components['username']}:{encoded_password}@{uri_components['host']}"
    test_connection_method(no_db_uri, "Without database")

def test_connection_method(uri, method_name):
    """Test a specific connection method."""
    try:
        print(f"   🔗 {method_name}: Connecting...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"   ✅ {method_name}: SUCCESS!")
        
        # Try to list databases
        db_names = client.list_database_names()
        print(f"   📊 Available databases: {db_names}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ {method_name}: {e}")
        return False

def main():
    """Main diagnostic function."""
    print("🚀 MongoDB Atlas Connection Diagnostics")
    print("=" * 60)
    
    # Get MongoDB URI
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment variables")
        return
    
    print(f"📋 Current MONGO_URI: {mongo_uri[:50]}...")
    
    # Parse URI
    uri_components = parse_mongo_uri(mongo_uri)
    
    # Test network connectivity
    test_network_connectivity()
    
    # Test different authentication methods
    test_different_auth_methods(uri_components)
    
    print("\n" + "=" * 60)
    print("🔧 TROUBLESHOOTING TIPS:")
    print("1. Check MongoDB Atlas dashboard for user permissions")
    print("2. Verify IP address is whitelisted (or use 0.0.0.0/0 for testing)")
    print("3. Ensure user has 'readWrite' role on the database")
    print("4. Check if password contains special characters that need encoding")
    print("5. Verify cluster is not paused or suspended")
    print("=" * 60)

if __name__ == "__main__":
    main()
