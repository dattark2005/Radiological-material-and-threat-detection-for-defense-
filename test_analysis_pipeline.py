#!/usr/bin/env python3
"""
Test the complete analysis pipeline
"""

import requests
import json
import time

def test_analysis_pipeline():
    """Test the complete analysis pipeline."""
    
    print("🧪 Testing Complete Analysis Pipeline")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Login
    print("🔐 Step 1: Authentication...")
    login_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()['token']
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Authentication successful")
        else:
            print(f"   ❌ Authentication failed: {login_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False
    
    # Step 2: Generate synthetic data
    print("\n📊 Step 2: Generate synthetic spectrum...")
    synthetic_data = {
        "isotope": "U-238",
        "noise_level": 2
    }
    
    try:
        synthetic_response = requests.post(
            f"{base_url}/api/upload/synthetic", 
            json=synthetic_data, 
            headers=headers
        )
        print(f"   Synthetic generation status: {synthetic_response.status_code}")
        
        if synthetic_response.status_code == 200:
            spectrum_data = synthetic_response.json()['spectrum_data']
            print(f"   ✅ Generated spectrum with {len(spectrum_data['counts'])} data points")
            print(f"   Isotope: {spectrum_data['isotope']}")
            print(f"   Total counts: {spectrum_data['total_counts']}")
        else:
            print(f"   ❌ Synthetic generation failed: {synthetic_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Synthetic generation error: {e}")
        return False
    
    # Step 3: Run analysis
    print("\n🔬 Step 3: Run ML analysis...")
    analysis_data = {
        "spectrum_data": spectrum_data
    }
    
    try:
        analysis_response = requests.post(
            f"{base_url}/api/analysis/run", 
            json=analysis_data, 
            headers=headers
        )
        print(f"   Analysis request status: {analysis_response.status_code}")
        
        if analysis_response.status_code in [200, 202]:
            analysis_result = analysis_response.json()
            session_id = analysis_result.get('session_id')
            print(f"   ✅ Analysis started with session ID: {session_id}")
            
            # Step 4: Check analysis status
            print("\n⏳ Step 4: Monitor analysis progress...")
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    status_response = requests.get(
                        f"{base_url}/api/analysis/status/{session_id}", 
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        progress = status_data.get('progress', 0)
                        
                        print(f"   Attempt {attempt + 1}: Status = {status}, Progress = {progress}%")
                        
                        if status == 'completed':
                            print("   ✅ Analysis completed!")
                            
                            # Step 5: Get results
                            print("\n📋 Step 5: Retrieve analysis results...")
                            results_response = requests.get(
                                f"{base_url}/api/analysis/results/{session_id}", 
                                headers=headers
                            )
                            
                            if results_response.status_code == 200:
                                results = results_response.json()
                                print("   ✅ Results retrieved successfully!")
                                print(f"   Classical prediction: {results.get('classical', {}).get('prediction', 'N/A')}")
                                print(f"   Classical confidence: {results.get('classical', {}).get('confidence', 'N/A')}")
                                print(f"   Quantum prediction: {results.get('quantum', {}).get('prediction', 'N/A')}")
                                print(f"   Quantum confidence: {results.get('quantum', {}).get('confidence', 'N/A')}")
                                print(f"   Threat level: {results.get('threat_assessment', {}).get('level', 'N/A')}")
                                return True
                            else:
                                print(f"   ❌ Failed to retrieve results: {results_response.text}")
                                return False
                        
                        elif status == 'failed':
                            print(f"   ❌ Analysis failed: {status_data.get('error', 'Unknown error')}")
                            return False
                        
                        time.sleep(2)
                        attempt += 1
                    else:
                        print(f"   ❌ Status check failed: {status_response.text}")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Status check error: {e}")
                    attempt += 1
                    time.sleep(2)
            
            print("   ⏰ Analysis timed out")
            return False
            
        else:
            print(f"   ❌ Analysis request failed: {analysis_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")
        return False

if __name__ == "__main__":
    success = test_analysis_pipeline()
    if success:
        print("\n🎉 Complete pipeline test SUCCESSFUL!")
    else:
        print("\n❌ Pipeline test FAILED!")
