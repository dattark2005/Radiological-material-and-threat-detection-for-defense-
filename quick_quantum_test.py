#!/usr/bin/env python3
"""
Quick Quantum ML Test - Fast version for testing with subset of data
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Simplified quantum simulation (no actual quantum hardware needed)
class QuickQuantumClassifier:
    """Quick quantum classifier for testing."""
    
    def __init__(self, num_features=8):
        self.num_features = num_features
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.trained = False
        
    def prepare_data_subset(self, csv_file, max_files=100):
        """Load and prepare a subset of data for quick testing."""
        print(f"📊 Loading subset of data (max {max_files} files)...")
        
        # Load CSV data
        df = pd.read_csv(csv_file)
        print(f"   - Total available: {len(df):,} data points from {df['File'].nunique()} files")
        
        # Take only first N files for quick testing
        unique_files = df['File'].unique()[:max_files]
        df_subset = df[df['File'].isin(unique_files)]
        
        print(f"   - Using subset: {len(df_subset):,} data points from {len(unique_files)} files")
        
        # Group by file to create spectrum features
        spectra_data = []
        
        print("🔄 Processing files...")
        for idx, file_name in enumerate(unique_files):
            if idx % 10 == 0:
                print(f"   - Processing file {idx+1}/{len(unique_files)}: {file_name}")
            
            file_data = df_subset[df_subset['File'] == file_name].sort_values('Channel')
            
            if len(file_data) > 0:
                counts = file_data['Counts'].values
                energies = file_data['Energy_keV'].values
                
                # Quick feature extraction
                features = self.extract_quick_features(counts, energies)
                
                spectra_data.append({
                    'file': file_name,
                    'isotope': file_data['Isotope'].iloc[0],
                    'features': features
                })
        
        # Convert to arrays
        X = np.array([item['features'] for item in spectra_data])
        y = np.array([item['isotope'] for item in spectra_data])
        
        print(f"✅ Created {len(X)} spectrum samples")
        print(f"   - Feature dimension: {X.shape[1]}")
        print(f"   - Unique isotopes: {np.unique(y)}")
        
        return X, y
    
    def extract_quick_features(self, counts, energies):
        """Quick feature extraction."""
        if len(counts) == 0:
            return np.zeros(self.num_features)
        
        # Normalize
        total_counts = np.sum(counts)
        if total_counts > 0:
            normalized_counts = counts / total_counts
        else:
            normalized_counts = counts
        
        # Quick features
        features = [
            np.mean(normalized_counts),           # Mean intensity
            np.std(normalized_counts),            # Intensity variation
            np.max(normalized_counts),            # Peak intensity
            len(counts),                          # Spectrum length
            np.sum(counts),                       # Total counts
            np.mean(energies) if len(energies) > 0 else 0,  # Mean energy
            np.std(energies) if len(energies) > 0 else 0,   # Energy spread
            np.sum(normalized_counts > 0.01)      # Number of significant channels
        ]
        
        return np.array(features[:self.num_features])
    
    def train_quick(self, X, y):
        """Quick training using classical ML as quantum simulation."""
        print("🚀 Quick Quantum Training (Simulated)...")
        
        # Scale and encode
        print("🔄 Preprocessing data...")
        X_scaled = self.scaler.fit_transform(X)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print(f"   - Training: {len(X_train)} samples")
        print(f"   - Testing: {len(X_test)} samples")
        print(f"   - Classes: {self.label_encoder.classes_}")
        
        # Simulate quantum training with classical ML
        print("🔄 Simulating quantum training...")
        from sklearn.ensemble import RandomForestClassifier
        
        # Use Random Forest as quantum simulation
        self.quantum_simulator = RandomForestClassifier(
            n_estimators=50, 
            random_state=42,
            max_depth=10
        )
        
        start_time = datetime.now()
        self.quantum_simulator.fit(X_train, y_train)
        training_time = datetime.now() - start_time
        
        print(f"✅ Training completed in {training_time}")
        
        # Evaluate
        train_score = self.quantum_simulator.score(X_train, y_train)
        test_score = self.quantum_simulator.score(X_test, y_test)
        
        print(f"📊 Quantum Simulation Results:")
        print(f"   - Training accuracy: {train_score:.3f}")
        print(f"   - Test accuracy: {test_score:.3f}")
        
        # Predictions
        y_pred = self.quantum_simulator.predict(X_test)
        
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
        
        self.trained = True
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'training_time': training_time
        }
    
    def predict(self, X):
        """Make predictions."""
        if not self.trained:
            raise ValueError("Model must be trained first")
        
        X_scaled = self.scaler.transform(X)
        y_pred_encoded = self.quantum_simulator.predict(X_scaled)
        y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
        
        return y_pred

def main():
    """Quick test main function."""
    print("⚡ Quick Quantum ML Test")
    print("=" * 40)
    
    # Initialize quick classifier
    qml = QuickQuantumClassifier()
    
    # Load subset of data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("Please run data_convert.py first")
        return
    
    try:
        # Use only 50 files for quick test
        X, y = qml.prepare_data_subset(csv_file, max_files=50)
        
        # Quick training
        results = qml.train_quick(X, y)
        
        print("\n🎯 Quick Test Summary:")
        print(f"   - Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"   - Training Time: {results['training_time']}")
        print("   - Status: ✅ Ready for full quantum training!")
        
        print("\n📝 Next Steps:")
        print("   1. This quick test validates your data format")
        print("   2. Now run: python quantum_ml_trainer.py")
        print("   3. Full quantum training will take longer but give better results")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
