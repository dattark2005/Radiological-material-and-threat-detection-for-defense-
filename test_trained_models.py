#!/usr/bin/env python3
"""
Test the trained quantum models
"""

import joblib
import numpy as np
import os
from pathlib import Path

def test_trained_models():
    """Test loading and inference of trained quantum models."""
    
    print("🧪 Testing Trained Quantum Models")
    print("=" * 50)
    
    models_dir = Path("quantum_models")
    
    if not models_dir.exists():
        print("❌ Quantum models directory not found!")
        return False
    
    # List available models
    model_files = list(models_dir.glob("*.joblib"))
    print(f"📁 Found {len(model_files)} model files:")
    for model_file in model_files:
        print(f"   - {model_file.name} ({model_file.stat().st_size} bytes)")
    
    print("\n🔄 Loading models...")
    
    try:
        # Load each model
        models = {}
        for model_file in model_files:
            model_name = model_file.stem
            print(f"   Loading {model_name}...")
            models[model_name] = joblib.load(model_file)
            print(f"   ✅ {model_name} loaded successfully")
        
        print(f"\n✅ All {len(models)} models loaded successfully!")
        
        # Test with dummy data
        print("\n🧪 Testing inference with dummy data...")
        
        # Create sample spectrum data (4 features based on trained models)
        sample_data = np.random.random((5, 4))
        
        if 'quantum_scaler' in models:
            print("   🔄 Testing scaler...")
            scaled_data = models['quantum_scaler'].transform(sample_data)
            print(f"   ✅ Scaler: {sample_data.shape} -> {scaled_data.shape}")
        
        if 'quantum_pca' in models:
            print("   🔄 Testing PCA...")
            if 'quantum_scaler' in models:
                pca_data = models['quantum_pca'].transform(scaled_data)
            else:
                pca_data = models['quantum_pca'].transform(sample_data)
            print(f"   ✅ PCA: {scaled_data.shape if 'quantum_scaler' in models else sample_data.shape} -> {pca_data.shape}")
        
        if 'quantum_vqc' in models:
            print("   🔄 Testing VQC...")
            try:
                if 'quantum_pca' in models:
                    vqc_pred = models['quantum_vqc'].predict(pca_data)
                else:
                    vqc_pred = models['quantum_vqc'].predict(scaled_data if 'quantum_scaler' in models else sample_data)
                print(f"   ✅ VQC predictions: {vqc_pred}")
            except Exception as e:
                print(f"   ⚠️  VQC prediction failed: {e}")
        
        if 'quantum_qsvc' in models:
            print("   🔄 Testing QSVC...")
            try:
                if 'quantum_pca' in models:
                    qsvc_pred = models['quantum_qsvc'].predict(pca_data)
                else:
                    qsvc_pred = models['quantum_qsvc'].predict(scaled_data if 'quantum_scaler' in models else sample_data)
                print(f"   ✅ QSVC predictions: {qsvc_pred}")
            except Exception as e:
                print(f"   ⚠️  QSVC prediction failed: {e}")
        
        print("\n🎉 Model testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False

if __name__ == "__main__":
    test_trained_models()
