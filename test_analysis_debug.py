#!/usr/bin/env python3
"""
Test analysis pipeline with debug information
"""

import requests
import json
import time

def test_analysis_with_debug():
    """Test analysis and show debug information."""
    
    print("🧪 Testing Analysis with Debug Information")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Login
    print("🔐 Step 1: Login...")
    login_data = {"username": "admin@example.com", "password": "admin123"}
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()['token']
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Step 2: Generate synthetic data
    print("\n📊 Step 2: Generate synthetic spectrum...")
    synthetic_data = {"isotope": "Cs-137", "noise_level": 1}
    
    try:
        synthetic_response = requests.post(
            f"{base_url}/api/upload/synthetic", 
            json=synthetic_data, 
            headers=headers
        )
        if synthetic_response.status_code == 200:
            spectrum_data = synthetic_response.json()['spectrum_data']
            print(f"   ✅ Generated spectrum with {len(spectrum_data['counts'])} data points")
        else:
            print(f"   ❌ Synthetic generation failed: {synthetic_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Synthetic generation error: {e}")
        return
    
    # Step 3: Run analysis
    print("\n🔬 Step 3: Run analysis...")
    analysis_data = {"spectrum_data": spectrum_data, "analysis_type": "quantum"}
    
    try:
        analysis_response = requests.post(
            f"{base_url}/api/analysis/run", 
            json=analysis_data, 
            headers=headers
        )
        print(f"   Analysis response status: {analysis_response.status_code}")
        print(f"   Analysis response: {analysis_response.text}")
        
        if analysis_response.status_code in [200, 202]:
            result = analysis_response.json()
            session_id = result.get('session_id')
            print(f"   ✅ Analysis started with session: {session_id}")
            
            # Step 4: Monitor status
            print("\n⏳ Step 4: Monitor analysis...")
            for i in range(10):  # Check 10 times
                time.sleep(2)
                try:
                    status_response = requests.get(
                        f"{base_url}/api/analysis/status/{session_id}", 
                        headers=headers
                    )
                    print(f"   Check {i+1}: Status = {status_response.status_code}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        print(f"   Status: {status}")
                        
                        if status == 'completed':
                            print("   ✅ Analysis completed!")
                            break
                        elif status == 'failed':
                            error_msg = status_data.get('error_message', 'Unknown error')
                            print(f"   ❌ Analysis failed: {error_msg}")
                            break
                    else:
                        print(f"   Status check failed: {status_response.text}")
                except Exception as e:
                    print(f"   Status check error: {e}")
            
        else:
            print(f"   ❌ Analysis start failed: {analysis_response.text}")
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")

if __name__ == "__main__":
    test_analysis_with_debug()
