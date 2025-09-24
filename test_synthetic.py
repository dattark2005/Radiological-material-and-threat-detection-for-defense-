#!/usr/bin/env python3
"""
Test script to debug synthetic spectrum generation
"""

import requests
import json

# Test the synthetic endpoint
def test_synthetic_endpoint():
    base_url = "http://localhost:5000"
    
    # First, login to get a token
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    print("[TEST] Logging in...")
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"[TEST] Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"[ERROR] Login failed: {login_response.text}")
        return
    
    login_json = login_response.json()
    print(f"[TEST] Login response: {login_json}")
    
    token = login_json.get('token')
    if not token:
        print(f"[ERROR] No access token in response")
        return
        
    print(f"[TEST] Got token: {token[:20]}...")
    
    # Test synthetic generation
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    synthetic_data = {
        "isotope": "Cs-137",
        "noise_level": 1
    }
    
    print(f"[TEST] Sending synthetic request: {synthetic_data}")
    synthetic_response = requests.post(f"{base_url}/api/upload/synthetic", 
                                     json=synthetic_data, 
                                     headers=headers)
    
    print(f"[TEST] Synthetic status: {synthetic_response.status_code}")
    print(f"[TEST] Synthetic response: {synthetic_response.text}")

if __name__ == "__main__":
    test_synthetic_endpoint()
