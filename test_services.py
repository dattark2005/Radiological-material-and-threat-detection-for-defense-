#!/usr/bin/env python3
"""
Test the ML services directly
"""

import sys
import os
sys.path.append('backend')

def test_services():
    """Test ML services directly."""
    
    print("🧪 Testing ML Services")
    print("=" * 40)
    
    # Test spectrum data
    spectrum_data = {
        'energy': list(range(0, 2000, 10)),  # 0-2000 keV
        'counts': [100 + i*0.1 for i in range(200)]  # Sample counts
    }
    
    print(f"📊 Test spectrum: {len(spectrum_data['energy'])} energy points")
    
    # Test Classical ML Service
    print("\n🔬 Testing Classical ML Service...")
    try:
        from backend.services.ml_service import ClassicalMLService
        classical_service = ClassicalMLService()
        classical_result = classical_service.analyze(spectrum_data)
        print("   ✅ Classical ML Service works")
        print(f"   Result keys: {list(classical_result.keys())}")
    except Exception as e:
        print(f"   ❌ Classical ML Service failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    
    # Test Quantum ML Service
    print("\n⚛️  Testing Quantum ML Service...")
    try:
        from backend.services.real_quantum_service import RealQuantumMLService
        quantum_service = RealQuantumMLService()
        quantum_result = quantum_service.analyze(spectrum_data)
        print("   ✅ Quantum ML Service works")
        print(f"   Result keys: {list(quantum_result.keys())}")
    except Exception as e:
        print(f"   ❌ Quantum ML Service failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    
    # Test Threat Assessment Service
    print("\n🚨 Testing Threat Assessment Service...")
    try:
        from backend.services.threat_service import ThreatAssessmentService
        threat_service = ThreatAssessmentService()
        
        # Mock results for testing
        mock_results = [{
            'threat_probability': 0.7,
            'classified_isotope': 'Cs-137',
            'confidence_level': 0.8
        }]
        
        threat_result = threat_service.assess_threat(mock_results)
        print("   ✅ Threat Assessment Service works")
        print(f"   Result keys: {list(threat_result.keys())}")
    except Exception as e:
        print(f"   ❌ Threat Assessment Service failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_services()
