#!/usr/bin/env python3
"""
Quantum Machine Learning Trainer for Radiological Threat Detection
Using Qiskit for Quantum Neural Networks (QNN) and Variational Quantum Classifier (VQC)
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import joblib
import os

# Qiskit imports for Quantum ML
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.primitives import Sampler
from qiskit_machine_learning.neural_networks import SamplerQNN
from qiskit_machine_learning.algorithms.classifiers import VQC
from qiskit.circuit.library import RealAmplitudes, ZZFeatureMap
from qiskit_algorithms.optimizers import COBYLA, SPSA, L_BFGS_B

class QuantumRadiologicalClassifier:
    """Quantum ML classifier for radiological threat detection."""
    
    def __init__(self, num_features=8, num_qubits=4):
        self.num_features = num_features
        self.num_qubits = num_qubits
        self.feature_map = None
        self.ansatz = None
        self.vqc = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.trained = False
        
    def create_quantum_circuit(self):
        """Create quantum feature map and ansatz."""
        print("🔬 Creating quantum circuits...")
        
        # Feature map for encoding classical data into quantum states
        self.feature_map = ZZFeatureMap(
            feature_dimension=self.num_features,
            reps=2,
            entanglement='linear'
        )
        
        # Variational ansatz for learning
        self.ansatz = RealAmplitudes(
            num_qubits=self.num_features,
            reps=3,
            entanglement='linear'
        )
        
        print(f"✅ Quantum circuits created:")
        print(f"   - Feature map: {self.feature_map.num_qubits} qubits, {self.feature_map.num_parameters} parameters")
        print(f"   - Ansatz: {self.ansatz.num_qubits} qubits, {self.ansatz.num_parameters} parameters")
        
    def prepare_data(self, csv_file):
        """Load and prepare data for quantum ML."""
        print("📊 Loading and preparing data...")
        
        # Load CSV data
        df = pd.read_csv(csv_file)
        print(f"   - Loaded {len(df):,} data points from {df['File'].nunique()} files")
        
        # Group by file to create spectrum features
        spectra_data = []
        unique_files = df['File'].unique()
        total_files = len(unique_files)
        
        print(f"🔄 Processing {total_files} spectrum files...")
        print("   Progress: [", end="", flush=True)
        
        for idx, file_name in enumerate(unique_files):
            # Show progress every 100 files
            if idx % 100 == 0:
                print("█", end="", flush=True)
            elif idx % 20 == 0:
                print("▓", end="", flush=True)
            elif idx % 10 == 0:
                print("░", end="", flush=True)
            
            # Show detailed progress every 200 files
            if idx % 200 == 0 and idx > 0:
                progress_pct = (idx / total_files) * 100
                print(f"] {progress_pct:.1f}% ({idx}/{total_files})")
                print(f"   - Processing file: {file_name}")
                print("   Progress: [", end="", flush=True)
            
            file_data = df[df['File'] == file_name].sort_values('Channel')
            
            if len(file_data) > 0:
                # Extract features from spectrum
                counts = file_data['Counts'].values
                energies = file_data['Energy_keV'].values
                
                # Feature engineering for quantum ML
                features = self.extract_quantum_features(counts, energies)
                
                spectra_data.append({
                    'file': file_name,
                    'isotope': file_data['Isotope'].iloc[0],
                    'detector': file_data['Detector'].iloc[0],
                    'features': features
                })
        
        print("] 100% Complete!")
        print(f"✅ Feature extraction completed for {len(spectra_data)} spectra")
        
        # Convert to arrays
        print("🔄 Converting to numpy arrays...")
        X = np.array([item['features'] for item in spectra_data])
        y = np.array([item['isotope'] for item in spectra_data])
        
        print(f"   - Created {len(X)} spectrum samples")
        print(f"   - Feature dimension: {X.shape[1]}")
        print(f"   - Unique isotopes: {np.unique(y)}")
        print(f"   - Memory usage: ~{X.nbytes / 1024 / 1024:.1f} MB")
        
        return X, y, spectra_data
    
    def extract_quantum_features(self, counts, energies):
        """Extract quantum-optimized features from gamma spectrum."""
        # Normalize counts
        total_counts = np.sum(counts)
        if total_counts == 0:
            normalized_counts = counts
        else:
            normalized_counts = counts / total_counts
        
        # Extract key features for quantum processing
        features = []
        
        # 1. Peak detection features
        peaks = self.find_significant_peaks(counts, energies)
        features.extend([
            len(peaks),  # Number of peaks
            np.mean([p['energy'] for p in peaks]) if peaks else 0,  # Mean peak energy
            np.std([p['energy'] for p in peaks]) if len(peaks) > 1 else 0,  # Peak energy spread
        ])
        
        # 2. Energy distribution features
        features.extend([
            np.mean(energies),  # Mean energy
            np.std(energies),   # Energy spread
            np.sum(normalized_counts * energies),  # Weighted mean energy
        ])
        
        # 3. Spectral shape features
        features.extend([
            np.sum(normalized_counts**2),  # Spectral concentration
            np.max(normalized_counts),     # Peak intensity
        ])
        
        return np.array(features[:self.num_features])
    
    def find_significant_peaks(self, counts, energies, threshold=0.1):
        """Find significant peaks in gamma spectrum."""
        if len(counts) == 0:
            return []
        
        max_count = np.max(counts)
        min_height = max_count * threshold
        
        peaks = []
        # Optimized peak detection - skip if too many points
        step = max(1, len(counts) // 1000)  # Sample every nth point for large spectra
        
        for i in range(step, len(counts)-step, step):
            if (counts[i] > counts[i-step] and 
                counts[i] > counts[i+step] and 
                counts[i] > min_height):
                peaks.append({
                    'channel': i,
                    'energy': energies[i] if i < len(energies) else i * 0.075,
                    'intensity': counts[i]
                })
        
        return peaks[:20]  # Limit to top 20 peaks for performance
    
    def train(self, X, y, test_size=0.2, optimizer='COBYLA'):
        """Train the quantum classifier."""
        print("🚀 Training Quantum ML model...")
        
        # Prepare data
        print("🔄 Scaling features...")
        X_scaled = self.scaler.fit_transform(X)
        print("🔄 Encoding labels...")
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split data
        print("🔄 Splitting data into train/test sets...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
        )
        
        print(f"   - Training set: {len(X_train)} samples")
        print(f"   - Test set: {len(X_test)} samples")
        print(f"   - Classes: {self.label_encoder.classes_}")
        
        # Create quantum circuits
        print("🔄 Creating quantum circuits...")
        self.create_quantum_circuit()
        
        # Choose optimizer
        optimizers = {
            'COBYLA': COBYLA(maxiter=50),  # Reduced iterations for faster training
            'SPSA': SPSA(maxiter=50),
            'L_BFGS_B': L_BFGS_B(maxiter=50)
        }
        
        # Create and train VQC
        print(f"🔄 Initializing VQC with {optimizer} optimizer...")
        self.vqc = VQC(
            feature_map=self.feature_map,
            ansatz=self.ansatz,
            optimizer=optimizers[optimizer],
            sampler=Sampler()
        )
        
        # Train the model
        print("🔄 Training quantum model...")
        print("   ⏱️  This may take 5-15 minutes depending on data size")
        print("   🎯 Optimizing quantum parameters...")
        start_time = datetime.now()
        
        self.vqc.fit(X_train, y_train)
        
        training_time = datetime.now() - start_time
        print(f"   ✅ Training completed in {training_time}")
        
        # Evaluate model
        print("🔄 Evaluating model performance...")
        train_score = self.vqc.score(X_train, y_train)
        test_score = self.vqc.score(X_test, y_test)
        
        print(f"✅ Quantum Model Performance:")
        print(f"   - Training accuracy: {train_score:.3f}")
        print(f"   - Test accuracy: {test_score:.3f}")
        
        # Detailed evaluation
        print("🔄 Generating predictions for detailed analysis...")
        y_pred = self.vqc.predict(X_test)
        
        print("\n📊 Detailed Classification Report:")
        print(classification_report(
            y_test, y_pred, 
            target_names=self.label_encoder.classes_
        ))
        
        # Confusion matrix
        print("🔄 Creating confusion matrix...")
        cm = confusion_matrix(y_test, y_pred)
        self.plot_confusion_matrix(cm, self.label_encoder.classes_)
        
        self.trained = True
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'training_time': training_time,
            'confusion_matrix': cm
        }
    
    def plot_confusion_matrix(self, cm, class_names):
        """Plot confusion matrix."""
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=class_names, yticklabels=class_names)
        plt.title('Quantum ML - Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig('quantum_confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("📈 Confusion matrix saved as 'quantum_confusion_matrix.png'")
    
    def predict(self, X):
        """Make predictions with the trained quantum model."""
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_scaled = self.scaler.transform(X)
        y_pred_encoded = self.vqc.predict(X_scaled)
        y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
        
        return y_pred
    
    def predict_proba(self, X):
        """Get prediction probabilities (if supported)."""
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_scaled = self.scaler.transform(X)
        # Note: VQC might not support predict_proba, implement custom scoring
        return self.vqc.predict(X_scaled)
    
    def save_model(self, filepath):
        """Save the trained quantum model."""
        if not self.trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'vqc_params': self.vqc.get_params(),
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'num_features': self.num_features,
            'num_qubits': self.num_qubits,
            'trained': self.trained
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 Quantum model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load a trained quantum model."""
        model_data = joblib.load(filepath)
        
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.num_features = model_data['num_features']
        self.num_qubits = model_data['num_qubits']
        self.trained = model_data['trained']
        
        # Recreate VQC (parameters will need to be set separately)
        self.create_quantum_circuit()
        
        print(f"📂 Quantum model loaded from {filepath}")

def main():
    """Main training pipeline."""
    print("🌟 Quantum ML Radiological Threat Detection Training")
    print("=" * 60)
    
    # Initialize quantum classifier
    qml = QuantumRadiologicalClassifier(num_features=8, num_qubits=4)
    
    # Load and prepare data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("Please run data_convert.py first to convert SPE files to CSV")
        return
    
    try:
        X, y, spectra_data = qml.prepare_data(csv_file)
        
        # Train quantum model
        results = qml.train(X, y, optimizer='COBYLA')
        
        # Save model
        model_path = "models/quantum_radiological_classifier.joblib"
        os.makedirs("models", exist_ok=True)
        qml.save_model(model_path)
        
        print("\n🎯 Training Summary:")
        print(f"   - Dataset: {len(X)} spectra")
        print(f"   - Features: {X.shape[1]}")
        print(f"   - Classes: {len(np.unique(y))}")
        print(f"   - Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"   - Training Time: {results['training_time']}")
        print(f"   - Model saved: {model_path}")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
