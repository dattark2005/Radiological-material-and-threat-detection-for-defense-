#!/usr/bin/env python3
"""
Balanced Quantum ML - Specifically designed for your imbalanced dataset
Addresses the 12:1 class imbalance and signal quality issues
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_class_weight
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import find_peaks
import os
from datetime import datetime

class BalancedQuantumML:
    """Quantum ML specifically designed for imbalanced radiological data."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.trained = False
        
    def extract_discriminative_features(self, counts, energies):
        """Extract features that discriminate between U, Pu, and MOX."""
        if len(counts) == 0 or len(energies) == 0:
            return np.zeros(15)
        
        # Ensure same length
        min_len = min(len(counts), len(energies))
        counts = counts[:min_len]
        energies = energies[:min_len]
        
        # Remove background (counts < 5% of max)
        max_count = np.max(counts)
        signal_mask = counts > (max_count * 0.05)
        
        if np.sum(signal_mask) == 0:
            return np.zeros(15)
        
        signal_counts = counts[signal_mask]
        signal_energies = energies[signal_mask]
        
        features = []
        
        # 1. Total activity features
        total_counts = np.sum(counts)
        features.extend([
            total_counts,
            np.log10(total_counts + 1),  # Log scale for wide range
            max_count,
            np.log10(max_count + 1)
        ])
        
        # 2. Energy-specific features (key for isotope discrimination)
        # Low energy region (0-100 keV) - Am-241, Pu signatures
        low_energy_mask = (energies >= 0) & (energies <= 100)
        low_energy_counts = np.sum(counts[low_energy_mask]) if np.any(low_energy_mask) else 0
        
        # Medium energy region (100-1000 keV) - Cs-137, Co-60
        med_energy_mask = (energies > 100) & (energies <= 1000)
        med_energy_counts = np.sum(counts[med_energy_mask]) if np.any(med_energy_mask) else 0
        
        # High energy region (>1000 keV) - High energy gammas
        high_energy_mask = energies > 1000
        high_energy_counts = np.sum(counts[high_energy_mask]) if np.any(high_energy_mask) else 0
        
        # Energy ratios (key discriminators)
        features.extend([
            low_energy_counts / (total_counts + 1),   # Low energy fraction
            med_energy_counts / (total_counts + 1),   # Medium energy fraction
            high_energy_counts / (total_counts + 1),  # High energy fraction
        ])
        
        # 3. Peak characteristics (different isotopes have different peak patterns)
        try:
            peaks, properties = find_peaks(counts, height=max_count*0.1, distance=20)
            if len(peaks) > 0:
                peak_energies = energies[peaks]
                peak_heights = properties['peak_heights']
                
                features.extend([
                    len(peaks),                           # Number of peaks
                    np.mean(peak_energies),              # Mean peak energy
                    np.std(peak_energies) if len(peaks) > 1 else 0,  # Peak energy spread
                    np.max(peak_heights) / (np.mean(counts) + 1),    # Peak prominence
                ])
            else:
                features.extend([0, 0, 0, 0])
        except:
            features.extend([0, 0, 0, 0])
        
        # 4. Spectral shape features
        # Spectral centroid (weighted mean energy)
        if total_counts > 0:
            spectral_centroid = np.sum(counts * energies) / total_counts
            # Spectral spread
            spectral_spread = np.sqrt(np.sum(counts * (energies - spectral_centroid)**2) / total_counts)
        else:
            spectral_centroid = 0
            spectral_spread = 0
        
        features.extend([
            spectral_centroid,
            spectral_spread,
            np.sum(counts > max_count * 0.1) / len(counts),  # Active channel fraction
        ])
        
        return np.array(features[:15])
    
    def prepare_balanced_data(self, df, balance_method='smote'):
        """Prepare balanced dataset addressing class imbalance."""
        print("🔄 Preparing balanced dataset...")
        
        # Extract features for all files
        spectra_data = []
        unique_files = df['File'].unique()
        
        print(f"   Processing {len(unique_files)} files...")
        print("   Progress: ", end="", flush=True)
        
        for idx, file_name in enumerate(unique_files):
            if idx % 100 == 0:
                print("█", end="", flush=True)
            elif idx % 20 == 0:
                print("▓", end="", flush=True)
            
            file_data = df[df['File'] == file_name].sort_values('Channel')
            
            if len(file_data) > 100:  # Ensure sufficient data
                counts = file_data['Counts'].values
                energies = file_data['Energy_keV'].values
                isotope = file_data['Isotope'].iloc[0]
                
                # Extract discriminative features
                features = self.extract_discriminative_features(counts, energies)
                
                # Add measurement context
                live_time = file_data['Live_Time_sec'].iloc[0] if 'Live_Time_sec' in file_data.columns else 900
                measurement_context = [
                    live_time,
                    len(file_data),  # Spectrum length
                ]
                
                # Combine features
                all_features = np.concatenate([features, measurement_context])
                
                spectra_data.append({
                    'file': file_name,
                    'isotope': isotope,
                    'features': all_features
                })
        
        print(" ✅")
        
        # Convert to arrays
        X = np.array([item['features'] for item in spectra_data])
        y = np.array([item['isotope'] for item in spectra_data])
        
        # Remove invalid features
        finite_mask = np.isfinite(X).all(axis=1)
        X = X[finite_mask]
        y = y[finite_mask]
        
        print(f"✅ Extracted features from {len(X)} spectra")
        print("   Class distribution before balancing:")
        unique, counts = np.unique(y, return_counts=True)
        for isotope, count in zip(unique, counts):
            print(f"     {isotope}: {count} samples ({count/len(y)*100:.1f}%)")
        
        # Apply balancing strategy
        if balance_method == 'smote':
            print("🔄 Applying SMOTE balancing...")
            from imblearn.over_sampling import SMOTE
            balancer = SMOTE(random_state=42, k_neighbors=3)
        elif balance_method == 'adasyn':
            print("🔄 Applying ADASYN balancing...")
            from imblearn.over_sampling import ADASYN
            balancer = ADASYN(random_state=42, n_neighbors=3)
        elif balance_method == 'smoteenn':
            print("🔄 Applying SMOTE+ENN balancing...")
            from imblearn.combine import SMOTEENN
            balancer = SMOTEENN(random_state=42)
        else:
            print("🔄 No balancing applied")
            return X, y
        
        try:
            X_balanced, y_balanced = balancer.fit_resample(X, y)
            
            print("   Class distribution after balancing:")
            unique, counts = np.unique(y_balanced, return_counts=True)
            for isotope, count in zip(unique, counts):
                print(f"     {isotope}: {count} samples ({count/len(y_balanced)*100:.1f}%)")
            
            return X_balanced, y_balanced
            
        except Exception as e:
            print(f"   ⚠️ Balancing failed: {e}")
            print("   Using original unbalanced data with class weights")
            return X, y
    
    def train_balanced_model(self, X, y):
        """Train model with balanced data and proper evaluation."""
        print("🚀 Training Balanced Quantum ML Model...")
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Calculate class weights for additional balancing
        classes = np.unique(y_encoded)
        class_weights = compute_class_weight('balanced', classes=classes, y=y_encoded)
        class_weight_dict = dict(zip(classes, class_weights))
        
        print(f"   Class weights: {dict(zip(self.label_encoder.classes_, class_weights))}")
        
        # Stratified split to maintain class balance
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print(f"   Training: {len(X_train)} samples")
        print(f"   Testing: {len(X_test)} samples")
        
        # Train ensemble with class balancing
        print("🔄 Training balanced ensemble...")
        
        # Multiple models with different strengths
        models = {
            'rf_balanced': RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                min_samples_split=3,
                min_samples_leaf=1,
                class_weight='balanced',
                random_state=42
            ),
            'rf_weighted': RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                min_samples_split=3,
                min_samples_leaf=1,
                class_weight=class_weight_dict,
                random_state=43
            )
        }
        
        # Train and evaluate each model
        best_model = None
        best_score = 0
        
        for name, model in models.items():
            print(f"   Training {name}...")
            model.fit(X_train, y_train)
            
            # Evaluate on validation set
            score = model.score(X_test, y_test)
            print(f"     {name} accuracy: {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_model = model
        
        self.model = best_model
        
        # Final evaluation
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"✅ Best Model Performance:")
        print(f"   - Training accuracy: {train_score:.3f}")
        print(f"   - Test accuracy: {test_score:.3f}")
        
        # Detailed per-class evaluation
        y_pred = self.model.predict(X_test)
        
        print("\n📊 Detailed Classification Report:")
        report = classification_report(y_test, y_pred, target_names=self.label_encoder.classes_, output_dict=True)
        print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
        
        # Per-class metrics
        print("\n🎯 Per-Class Performance:")
        for i, class_name in enumerate(self.label_encoder.classes_):
            if class_name in report:
                precision = report[class_name]['precision']
                recall = report[class_name]['recall']
                f1 = report[class_name]['f1-score']
                support = report[class_name]['support']
                print(f"   {class_name}: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f} (n={support})")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        self.plot_balanced_results(cm, self.label_encoder.classes_, report)
        
        self.trained = True
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'per_class_metrics': report
        }
    
    def save_model(self, filepath):
        """Save the trained model and preprocessing components."""
        if not self.trained:
            raise ValueError("Model must be trained before saving")
        
        import joblib
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'trained': self.trained,
            'model_type': 'balanced_quantum_ml',
            'timestamp': datetime.now().isoformat()
        }
        
        # Create models directory
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save model
        joblib.dump(model_data, filepath)
        print(f"💾 Model saved to: {filepath}")
        
        # Save model info
        info_file = filepath.replace('.joblib', '_info.txt')
        with open(info_file, 'w') as f:
            f.write("Balanced Quantum ML Model Information\n")
            f.write("=" * 40 + "\n")
            f.write(f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model Type: Balanced Random Forest Ensemble\n")
            f.write(f"Classes: {list(self.label_encoder.classes_)}\n")
            f.write(f"Features: {len(self.scaler.mean_)} dimensions\n")
            f.write(f"Balancing: SMOTE + Class Weights\n")
        
        print(f"📋 Model info saved to: {info_file}")
        
        return filepath
    
    def load_model(self, filepath):
        """Load a saved model."""
        import joblib
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.trained = model_data['trained']
        
        print(f"📂 Model loaded from: {filepath}")
        print(f"   Classes: {list(self.label_encoder.classes_)}")
        print(f"   Features: {len(self.scaler.mean_)} dimensions")
        
        return True
    
    def predict(self, X):
        """Make predictions with the trained model."""
        if not self.trained:
            raise ValueError("Model must be trained or loaded before making predictions")
        
        X_scaled = self.scaler.transform(X)
        y_pred_encoded = self.model.predict(X_scaled)
        y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
        
        return y_pred
    
    def predict_proba(self, X):
        """Get prediction probabilities."""
        if not self.trained:
            raise ValueError("Model must be trained or loaded before making predictions")
        
        X_scaled = self.scaler.transform(X)
        y_proba = self.model.predict_proba(X_scaled)
        
        return y_proba, self.label_encoder.classes_
    
    def plot_balanced_results(self, cm, class_names, report):
        """Plot results with focus on balanced performance."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Confusion Matrix
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names, ax=ax1)
        ax1.set_title('Confusion Matrix')
        ax1.set_xlabel('Predicted')
        ax1.set_ylabel('Actual')
        
        # 2. Per-class metrics
        metrics = ['precision', 'recall', 'f1-score']
        class_metrics = {metric: [] for metric in metrics}
        
        for class_name in class_names:
            if class_name in report:
                for metric in metrics:
                    class_metrics[metric].append(report[class_name][metric])
            else:
                for metric in metrics:
                    class_metrics[metric].append(0)
        
        x = np.arange(len(class_names))
        width = 0.25
        
        for i, metric in enumerate(metrics):
            ax2.bar(x + i*width, class_metrics[metric], width, label=metric, alpha=0.8)
        
        ax2.set_title('Per-Class Performance Metrics')
        ax2.set_xlabel('Isotope')
        ax2.set_ylabel('Score')
        ax2.set_xticks(x + width)
        ax2.set_xticklabels(class_names)
        ax2.legend()
        ax2.set_ylim(0, 1)
        
        # 3. Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_names = [f'Feature_{i}' for i in range(len(importances))]
            indices = np.argsort(importances)[::-1][:10]
            
            ax3.bar(range(len(indices)), importances[indices])
            ax3.set_title('Top 10 Feature Importances')
            ax3.set_xlabel('Feature Rank')
            ax3.set_ylabel('Importance')
        
        # 4. Class balance visualization
        original_counts = [972, 539, 80]  # From your analysis
        balanced_counts = [report[class_name]['support'] for class_name in class_names if class_name in report]
        
        x = np.arange(len(class_names))
        ax4.bar(x - 0.2, original_counts, 0.4, label='Original', alpha=0.7)
        ax4.bar(x + 0.2, balanced_counts, 0.4, label='Test Set', alpha=0.7)
        ax4.set_title('Class Distribution: Original vs Test')
        ax4.set_xlabel('Isotope')
        ax4.set_ylabel('Sample Count')
        ax4.set_xticks(x)
        ax4.set_xticklabels(class_names)
        ax4.legend()
        ax4.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig('balanced_quantum_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📈 Results saved as 'balanced_quantum_results.png'")

def create_deployment_script(model_path, results):
    """Create deployment script for the trained model."""
    deployment_code = f'''#!/usr/bin/env python3
"""
Deployment Script for Balanced Quantum ML Model
Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime

class DeployedQuantumModel:
    """Production-ready quantum ML model for radiological detection."""
    
    def __init__(self, model_path="{model_path}"):
        self.model_path = model_path
        self.model_data = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {{self.model_path}}")
        
        self.model_data = joblib.load(self.model_path)
        print(f"📂 Loaded model: {{self.model_data['model_type']}}")
        print(f"   Classes: {{list(self.model_data['label_encoder'].classes_)}}")
        print(f"   Accuracy: {results['test_accuracy']:.3f}")
    
    def extract_features(self, counts, energies):
        """Extract features from spectrum data."""
        if len(counts) == 0 or len(energies) == 0:
            return np.zeros(17)  # 15 + 2 context features
        
        # Ensure same length
        min_len = min(len(counts), len(energies))
        counts = counts[:min_len]
        energies = energies[:min_len]
        
        # Remove background
        max_count = np.max(counts)
        signal_mask = counts > (max_count * 0.05)
        
        if np.sum(signal_mask) == 0:
            return np.zeros(17)
        
        features = []
        
        # Total activity features
        total_counts = np.sum(counts)
        features.extend([
            total_counts,
            np.log10(total_counts + 1),
            max_count,
            np.log10(max_count + 1)
        ])
        
        # Energy-specific features
        low_energy_mask = (energies >= 0) & (energies <= 100)
        med_energy_mask = (energies > 100) & (energies <= 1000)
        high_energy_mask = energies > 1000
        
        low_counts = np.sum(counts[low_energy_mask]) if np.any(low_energy_mask) else 0
        med_counts = np.sum(counts[med_energy_mask]) if np.any(med_energy_mask) else 0
        high_counts = np.sum(counts[high_energy_mask]) if np.any(high_energy_mask) else 0
        
        features.extend([
            low_counts / (total_counts + 1),
            med_counts / (total_counts + 1),
            high_counts / (total_counts + 1),
        ])
        
        # Peak features (simplified)
        from scipy.signal import find_peaks
        try:
            peaks, properties = find_peaks(counts, height=max_count*0.1, distance=20)
            if len(peaks) > 0:
                peak_energies = energies[peaks]
                peak_heights = properties['peak_heights']
                
                features.extend([
                    len(peaks),
                    np.mean(peak_energies),
                    np.std(peak_energies) if len(peaks) > 1 else 0,
                    np.max(peak_heights) / (np.mean(counts) + 1),
                ])
            else:
                features.extend([0, 0, 0, 0])
        except:
            features.extend([0, 0, 0, 0])
        
        # Spectral features
        if total_counts > 0:
            spectral_centroid = np.sum(counts * energies) / total_counts
            spectral_spread = np.sqrt(np.sum(counts * (energies - spectral_centroid)**2) / total_counts)
        else:
            spectral_centroid = 0
            spectral_spread = 0
        
        features.extend([
            spectral_centroid,
            spectral_spread,
            np.sum(counts > max_count * 0.1) / len(counts),
        ])
        
        # Context features
        features.extend([
            900,  # Default live time
            len(counts),  # Spectrum length
        ])
        
        return np.array(features[:17])
    
    def predict_isotope(self, counts, energies):
        """Predict isotope from spectrum data."""
        # Extract features
        features = self.extract_features(counts, energies)
        
        # Scale features
        features_scaled = self.model_data['scaler'].transform([features])
        
        # Make prediction
        prediction_encoded = self.model_data['model'].predict(features_scaled)[0]
        prediction = self.model_data['label_encoder'].inverse_transform([prediction_encoded])[0]
        
        # Get probabilities
        probabilities = self.model_data['model'].predict_proba(features_scaled)[0]
        
        # Create result
        result = {{
            'predicted_isotope': prediction,
            'confidence': float(np.max(probabilities)),
            'probabilities': dict(zip(self.model_data['label_encoder'].classes_, probabilities)),
            'timestamp': datetime.now().isoformat(),
            'model_version': 'balanced_quantum_v1.0'
        }}
        
        return result
    
    def analyze_spectrum_file(self, csv_file, file_name):
        """Analyze a specific spectrum file."""
        df = pd.read_csv(csv_file)
        file_data = df[df['File'] == file_name].sort_values('Channel')
        
        if len(file_data) == 0:
            raise ValueError(f"File not found: {{file_name}}")
        
        counts = file_data['Counts'].values
        energies = file_data['Energy_keV'].values
        
        return self.predict_isotope(counts, energies)

# Example usage
if __name__ == "__main__":
    # Initialize model
    model = DeployedQuantumModel()
    
    # Test with your CSV data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if os.path.exists(csv_file):
        # Test on a few files
        df = pd.read_csv(csv_file)
        test_files = df['File'].unique()[:5]
        
        print("🧪 Testing deployed model:")
        for file_name in test_files:
            try:
                result = model.analyze_spectrum_file(csv_file, file_name)
                print(f"   {{file_name}}: {{result['predicted_isotope']}} ({{result['confidence']:.3f}})")
            except Exception as e:
                print(f"   {{file_name}}: Error - {{e}}")
    else:
        print("❌ CSV file not found for testing")
'''
    
    # Save deployment script
    with open("deploy_balanced_model.py", "w") as f:
        f.write(deployment_code)
    
    print("📄 Deployment script created: deploy_balanced_model.py")

def main():
    """Main balanced training pipeline."""
    print("⚖️ Balanced Quantum ML for Imbalanced Radiological Data")
    print("=" * 65)
    
    # Initialize balanced classifier
    bqml = BalancedQuantumML()
    
    # Load data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    try:
        # Load data
        print("📊 Loading data...")
        df = pd.read_csv(csv_file)
        
        # Prepare balanced dataset
        X, y = bqml.prepare_balanced_data(df, balance_method='smote')
        
        # Train balanced model
        results = bqml.train_balanced_model(X, y)
        
        print("\n🎯 Balanced Model Results:")
        print(f"   - Test Accuracy: {results['test_accuracy']:.3f}")
        
        # Check if MOX performance improved
        if 'MOX' in results['per_class_metrics']:
            mox_f1 = results['per_class_metrics']['MOX']['f1-score']
            print(f"   - MOX F1-Score: {mox_f1:.3f}")
            
            if mox_f1 > 0.5:
                print("🎉 Excellent! MOX detection significantly improved!")
            elif mox_f1 > 0.3:
                print("👍 Good improvement in MOX detection!")
            else:
                print("⚠️ MOX still challenging - need more advanced techniques")
        
        # Save the trained model
        print("\n💾 Saving trained model...")
        model_path = "models/balanced_quantum_radiological_classifier.joblib"
        saved_path = bqml.save_model(model_path)
        
        print(f"\n✅ Model Training Complete!")
        print(f"   - Model saved: {saved_path}")
        print(f"   - Ready for deployment!")
        
        # Create deployment script
        create_deployment_script(saved_path, results)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
