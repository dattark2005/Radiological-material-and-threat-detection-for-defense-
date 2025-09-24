#!/usr/bin/env python3
"""
Classical ML Model Training Pipeline for Radiological Threat Detection
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class ClassicalModelTrainer:
    """Train and evaluate classical ML models for radiological threat detection."""
    
    def __init__(self, data_path=None):
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_names = []
        self.results = {}
        
    def load_dataset(self, data_path):
        """Load and preprocess the radiological dataset."""
        print("[INFO] Loading radiological dataset...")
        
        # Load your dataset (CSV, JSON, or database)
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        elif data_path.endswith('.json'):
            df = pd.read_json(data_path)
        else:
            raise ValueError("Unsupported file format")
            
        return df
    
    def extract_features(self, spectrum_data):
        """Extract meaningful features from gamma-ray spectra."""
        features = []
        
        for spectrum in spectrum_data:
            energy = np.array(spectrum['energy_channels'])
            counts = np.array(spectrum['counts'])
            
            # Statistical features
            total_counts = np.sum(counts)
            max_count = np.max(counts)
            mean_energy = np.average(energy, weights=counts)
            std_energy = np.sqrt(np.average((energy - mean_energy)**2, weights=counts))
            
            # Peak detection features
            peaks = self.find_peaks(counts, energy)
            num_peaks = len(peaks)
            peak_energies = [p['energy'] for p in peaks]
            peak_intensities = [p['intensity'] for p in peaks]
            
            # Spectral shape features
            skewness = self.calculate_skewness(counts)
            kurtosis = self.calculate_kurtosis(counts)
            
            # Energy region features (low, medium, high energy)
            low_energy_counts = np.sum(counts[energy < 500])
            mid_energy_counts = np.sum(counts[(energy >= 500) & (energy < 1500)])
            high_energy_counts = np.sum(counts[energy >= 1500])
            
            feature_vector = [
                total_counts, max_count, mean_energy, std_energy,
                num_peaks, skewness, kurtosis,
                low_energy_counts, mid_energy_counts, high_energy_counts
            ]
            
            # Add peak features (pad/truncate to fixed size)
            peak_features = (peak_energies + [0]*5)[:5] + (peak_intensities + [0]*5)[:5]
            feature_vector.extend(peak_features)
            
            features.append(feature_vector)
            
        self.feature_names = [
            'total_counts', 'max_count', 'mean_energy', 'std_energy',
            'num_peaks', 'skewness', 'kurtosis',
            'low_energy_counts', 'mid_energy_counts', 'high_energy_counts',
            'peak1_energy', 'peak2_energy', 'peak3_energy', 'peak4_energy', 'peak5_energy',
            'peak1_intensity', 'peak2_intensity', 'peak3_intensity', 'peak4_intensity', 'peak5_intensity'
        ]
        
        return np.array(features)
    
    def find_peaks(self, counts, energy, threshold=0.1):
        """Find peaks in gamma-ray spectrum."""
        from scipy.signal import find_peaks as scipy_find_peaks
        
        peaks_idx, properties = scipy_find_peaks(counts, height=np.max(counts)*threshold)
        peaks = []
        
        for idx in peaks_idx:
            peaks.append({
                'energy': energy[idx],
                'intensity': counts[idx],
                'index': idx
            })
            
        return sorted(peaks, key=lambda x: x['intensity'], reverse=True)
    
    def calculate_skewness(self, data):
        """Calculate skewness of the spectrum."""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 3)
    
    def calculate_kurtosis(self, data):
        """Calculate kurtosis of the spectrum."""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 4) - 3
    
    def train_models(self, X, y):
        """Train multiple classical ML models."""
        print("[CLASSICAL] Training classical ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['standard'] = scaler
        
        # Define models
        models = {
            'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
            'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'SVM': SVC(kernel='rbf', probability=True, random_state=42),
            'NeuralNetwork': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
        }
        
        # Train and evaluate each model
        for name, model in models.items():
            print(f"Training {name}...")
            
            if name in ['SVM', 'NeuralNetwork']:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                y_prob = model.predict_proba(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_prob = model.predict_proba(X_test)
            
            # Evaluate
            accuracy = model.score(X_test_scaled if name in ['SVM', 'NeuralNetwork'] else X_test, y_test)
            cv_scores = cross_val_score(model, X_train_scaled if name in ['SVM', 'NeuralNetwork'] else X_train, y_train, cv=5)
            
            self.models[name] = model
            self.results[name] = {
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'predictions': y_pred,
                'probabilities': y_prob,
                'y_test': y_test
            }
            
            print(f"{name} - Accuracy: {accuracy:.4f}, CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        return X_test, y_test
    
    def save_models(self, save_dir='ml_models'):
        """Save trained models."""
        os.makedirs(save_dir, exist_ok=True)
        
        for name, model in self.models.items():
            model_path = os.path.join(save_dir, f'{name.lower()}_model.joblib')
            joblib.dump(model, model_path)
            print(f"[SAVED] {name} model to {model_path}")
        
        # Save scalers and encoders
        for name, scaler in self.scalers.items():
            scaler_path = os.path.join(save_dir, f'{name}_scaler.joblib')
            joblib.dump(scaler, scaler_path)
        
        # Save feature names
        feature_path = os.path.join(save_dir, 'feature_names.joblib')
        joblib.dump(self.feature_names, feature_path)
    
    def generate_report(self):
        """Generate training report."""
        print("\n[REPORT] TRAINING REPORT")
        print("=" * 50)
        
        for name, results in self.results.items():
            print(f"\n{name}:")
            print(f"  Accuracy: {results['accuracy']:.4f}")
            print(f"  Cross-validation: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
            
            # Classification report
            print(f"\n  Classification Report:")
            print(classification_report(results['y_test'], results['predictions']))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Classical ML Models for Radiological Threat Detection')
    parser.add_argument('--data', type=str, help='Path to dataset CSV file')
    
    args = parser.parse_args()
    
    trainer = ClassicalModelTrainer()
    
    if args.data:
        try:
            # Load dataset
            print(f"[INFO] Loading dataset from {args.data}")
            df = trainer.load_dataset(args.data)
            
            # Prepare features and labels
            feature_columns = ['total_counts', 'max_count', 'mean_count', 'std_count', 'skewness', 
                             'energy_range', 'weighted_mean_energy', 'num_peaks', 
                             'low_energy_fraction', 'mid_energy_fraction', 'high_energy_fraction', 'live_time']
            
            X = df[feature_columns].values
            y = df['threat_level'].values
            
            print(f"[SUCCESS] Loaded dataset: {X.shape[0]} samples, {X.shape[1]} features")
            print(f"[INFO] Classes: {np.unique(y)}")
            
            # Train models
            print("\n[INFO] Starting Classical ML Training...")
            trainer.train_models(X, y)
            
            # Save models
            trainer.save_models()
            
            # Generate report
            trainer.generate_report()
            
            print("\n[SUCCESS] Classical ML training completed!")
            
        except FileNotFoundError:
            print(f"[ERROR] Dataset file not found: {args.data}")
        except Exception as e:
            print(f"[ERROR] Error during training: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("Classical ML trainer ready for use!")
        print("Usage: python classical_trainer.py --data path/to/dataset.csv")
