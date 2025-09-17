#!/usr/bin/env python3
"""
Test Authentication API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

def test_login():
    """Test login endpoint with email as username."""
    print("🔐 Testing Login API...")
    
    # Test data - using email as username
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json().get('token')
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_register():
    """Test registration endpoint."""
    print("\n📝 Testing Registration API...")
    
    # Test data
    register_data = {
        "email": "test@example.com",
        "password": "Test123!",
        "username": "testuser"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
        else:
            print("❌ Registration failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Authentication API")
    print("=" * 40)
    
    # Test login first
    token = test_login()
    
    # Test registration
    test_register()
    
    print("=" * 40)
    print("🎯 Test completed!")
