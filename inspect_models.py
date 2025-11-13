#!/usr/bin/env python3
"""
Inspect the trained quantum models to understand their structure
"""

import joblib
import numpy as np
from pathlib import Path

def inspect_models():
    """Inspect the structure of trained quantum models."""
    
    print("🔍 Inspecting Trained Quantum Models")
    print("=" * 50)
    
    models_dir = Path("quantum_models")
    
    if not models_dir.exists():
        print("❌ Quantum models directory not found!")
        return False
    
    # Load and inspect each model
    model_files = list(models_dir.glob("*.joblib"))
    
    for model_file in model_files:
        print(f"\n📋 Inspecting {model_file.name}:")
        try:
            model = joblib.load(model_file)
            print(f"   Type: {type(model).__name__}")
            
            # Inspect different model types
            if hasattr(model, 'n_features_in_'):
                print(f"   Input features: {model.n_features_in_}")
            
            if hasattr(model, 'n_components_'):
                print(f"   Output components: {model.n_components_}")
            
            if hasattr(model, 'classes_'):
                print(f"   Classes: {model.classes_}")
            
            if hasattr(model, 'feature_names_in_'):
                print(f"   Feature names: {model.feature_names_in_}")
            
            if hasattr(model, 'n_features_'):
                print(f"   Features: {model.n_features_}")
                
            if hasattr(model, 'scale_'):
                print(f"   Scaler scale shape: {model.scale_.shape}")
                
            if hasattr(model, 'mean_'):
                print(f"   Scaler mean shape: {model.mean_.shape}")
                
            # For PCA
            if hasattr(model, 'components_'):
                print(f"   PCA components shape: {model.components_.shape}")
                
            print(f"   ✅ Model loaded successfully")
            
        except Exception as e:
            print(f"   ❌ Error loading model: {e}")
    
    print("\n🧪 Testing compatible pipeline...")
    
    try:
        # Load models
        scaler = joblib.load("quantum_models/quantum_scaler.joblib")
        pca = joblib.load("quantum_models/quantum_pca.joblib")
        vqc = joblib.load("quantum_models/quantum_vqc.joblib")
        qsvc = joblib.load("quantum_models/quantum_qsvc.joblib")
        
        # Test with correct dimensions
        print(f"   Scaler expects: {scaler.n_features_in_} features")
        
        # Create test data with correct dimensions
        test_data = np.random.random((3, scaler.n_features_in_))
        print(f"   Test data shape: {test_data.shape}")
        
        # Test pipeline
        scaled = scaler.transform(test_data)
        print(f"   After scaling: {scaled.shape}")
        
        pca_transformed = pca.transform(scaled)
        print(f"   After PCA: {pca_transformed.shape}")
        
        vqc_pred = vqc.predict(pca_transformed)
        print(f"   VQC predictions: {vqc_pred}")
        
        qsvc_pred = qsvc.predict(pca_transformed)
        print(f"   QSVC predictions: {qsvc_pred}")
        
        print("\n🎉 Pipeline test successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline test failed: {e}")
        return False

if __name__ == "__main__":
    inspect_models()
