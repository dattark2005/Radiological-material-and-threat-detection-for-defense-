#!/usr/bin/env python3
"""
Optimized Quantum ML for Radiological Detection
Better feature engineering and preprocessing for higher accuracy
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.signal import find_peaks
import os
from datetime import datetime

class OptimizedQuantumML:
    """Optimized Quantum ML with better feature engineering."""
    
    def __init__(self):
        self.scaler = RobustScaler()  # Better for outliers
        self.label_encoder = LabelEncoder()
        self.feature_selector = SelectKBest(f_classif, k=15)  # Select best features
        self.trained = False
        
    def load_and_analyze_data(self, csv_file):
        """Load data and perform exploratory analysis."""
        print("📊 Loading and analyzing data...")
        
        df = pd.read_csv(csv_file)
        print(f"   - Total data points: {len(df):,}")
        print(f"   - Unique files: {df['File'].nunique()}")
        print(f"   - Isotope distribution:")
        
        isotope_counts = df['Isotope'].value_counts()
        for isotope, count in isotope_counts.items():
            file_count = df[df['Isotope'] == isotope]['File'].nunique()
            print(f"     * {isotope}: {file_count} files")
        
        return df
    
    def extract_advanced_features(self, counts, energies):
        """Extract advanced spectral features for better classification."""
        if len(counts) == 0 or len(energies) == 0:
            return np.zeros(20)
        
        # Ensure same length
        min_len = min(len(counts), len(energies))
        counts = counts[:min_len]
        energies = energies[:min_len]
        
        # Remove zeros and normalize
        nonzero_mask = counts > 0
        if np.sum(nonzero_mask) == 0:
            return np.zeros(20)
        
        counts_nz = counts[nonzero_mask]
        energies_nz = energies[nonzero_mask]
        
        # Normalize counts
        total_counts = np.sum(counts)
        if total_counts > 0:
            normalized_counts = counts / total_counts
        else:
            normalized_counts = counts
        
        features = []
        
        # 1. Basic statistical features
        features.extend([
            np.mean(counts_nz),
            np.std(counts_nz),
            np.median(counts_nz),
            stats.skew(counts_nz),
            stats.kurtosis(counts_nz),
        ])
        
        # 2. Energy-weighted features
        if len(energies_nz) > 0:
            weighted_energy = np.average(energies_nz, weights=counts_nz)
            energy_variance = np.average((energies_nz - weighted_energy)**2, weights=counts_nz)
            features.extend([
                weighted_energy,
                np.sqrt(energy_variance),
                np.min(energies_nz),
                np.max(energies_nz),
                np.ptp(energies_nz)  # Peak-to-peak
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # 3. Peak detection features
        try:
            peaks, properties = find_peaks(counts, height=np.max(counts)*0.1, distance=10)
            features.extend([
                len(peaks),  # Number of peaks
                np.mean(properties['peak_heights']) if len(peaks) > 0 else 0,
                np.std(properties['peak_heights']) if len(peaks) > 1 else 0,
                np.mean(energies[peaks]) if len(peaks) > 0 else 0,
                np.std(energies[peaks]) if len(peaks) > 1 else 0,
            ])
        except:
            features.extend([0, 0, 0, 0, 0])
        
        # Pad or truncate to exactly 20 features
        features = np.array(features)
        if len(features) < 20:
            features = np.pad(features, (0, 20 - len(features)))
        else:
            features = features[:20]
        
        return features
    
    def prepare_optimized_data(self, df, sample_size=None):
        """Prepare data with advanced feature engineering."""
        print("🔄 Advanced feature engineering...")
        
        unique_files = df['File'].unique()
        if sample_size:
            unique_files = unique_files[:sample_size]
            print(f"   - Using sample of {len(unique_files)} files")
        
        spectra_data = []
        
        print("   Progress: ", end="", flush=True)
        for idx, file_name in enumerate(unique_files):
            if idx % 50 == 0:
                print("█", end="", flush=True)
            elif idx % 10 == 0:
                print("▓", end="", flush=True)
            
            file_data = df[df['File'] == file_name].sort_values('Channel')
            
            if len(file_data) > 10:  # Ensure minimum data points
                counts = file_data['Counts'].values
                energies = file_data['Energy_keV'].values
                
                # Advanced feature extraction
                features = self.extract_advanced_features(counts, energies)
                
                # Additional metadata features
                isotope = file_data['Isotope'].iloc[0]
                live_time = file_data['Live_Time_sec'].iloc[0] if 'Live_Time_sec' in file_data.columns else 900
                
                # Add context features
                context_features = [
                    len(file_data),  # Spectrum length
                    live_time,       # Measurement time
                    np.sum(counts),  # Total counts
                ]
                
                # Combine all features
                all_features = np.concatenate([features, context_features])
                
                spectra_data.append({
                    'file': file_name,
                    'isotope': isotope,
                    'features': all_features
                })
        
        print(" ✅")
        
        # Convert to arrays
        X = np.array([item['features'] for item in spectra_data])
        y = np.array([item['isotope'] for item in spectra_data])
        
        # Remove any NaN or infinite values
        finite_mask = np.isfinite(X).all(axis=1)
        X = X[finite_mask]
        y = y[finite_mask]
        
        print(f"✅ Created {len(X)} clean spectrum samples")
        print(f"   - Feature dimension: {X.shape[1]}")
        print(f"   - Isotope distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
        
        return X, y
    
    def train_optimized_model(self, X, y):
        """Train optimized model with better preprocessing."""
        print("🚀 Training Optimized Quantum ML Model...")
        
        # Handle class imbalance
        from sklearn.utils.class_weight import compute_class_weight
        
        classes = np.unique(y)
        class_weights = compute_class_weight('balanced', classes=classes, y=y)
        class_weight_dict = dict(zip(classes, class_weights))
        
        print(f"   - Class weights: {class_weight_dict}")
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Feature scaling
        print("🔄 Scaling features...")
        X_scaled = self.scaler.fit_transform(X)
        
        # Feature selection
        print("🔄 Selecting best features...")
        X_selected = self.feature_selector.fit_transform(X_scaled, y_encoded)
        
        selected_features = self.feature_selector.get_support()
        print(f"   - Selected {np.sum(selected_features)} out of {len(selected_features)} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_selected, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print(f"   - Training: {len(X_train)} samples")
        print(f"   - Testing: {len(X_test)} samples")
        
        # Train multiple models and ensemble
        print("🔄 Training ensemble models...")
        
        models = {
            'rf': RandomForestClassifier(
                n_estimators=200, 
                max_depth=15, 
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42
            ),
            'extra_trees': ExtraTreesClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42
            )
        }
        
        from sklearn.ensemble import ExtraTreesClassifier, VotingClassifier
        
        # Create voting classifier
        self.ensemble_model = VotingClassifier(
            estimators=list(models.items()),
            voting='soft'
        )
        
        start_time = datetime.now()
        self.ensemble_model.fit(X_train, y_train)
        training_time = datetime.now() - start_time
        
        print(f"✅ Training completed in {training_time}")
        
        # Evaluate
        train_score = self.ensemble_model.score(X_train, y_train)
        test_score = self.ensemble_model.score(X_test, y_test)
        
        print(f"📊 Optimized Model Performance:")
        print(f"   - Training accuracy: {train_score:.3f}")
        print(f"   - Test accuracy: {test_score:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.ensemble_model, X_selected, y_encoded, cv=5)
        print(f"   - Cross-validation: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Detailed evaluation
        y_pred = self.ensemble_model.predict(X_test)
        
        print("\n📋 Detailed Classification Report:")
        print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        self.plot_results(cm, self.label_encoder.classes_, cv_scores)
        
        self.trained = True
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'training_time': training_time
        }
    
    def plot_results(self, cm, class_names, cv_scores):
        """Plot comprehensive results."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Confusion Matrix
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names, ax=ax1)
        ax1.set_title('Confusion Matrix')
        ax1.set_xlabel('Predicted')
        ax1.set_ylabel('Actual')
        
        # Cross-validation scores
        ax2.bar(range(len(cv_scores)), cv_scores, color='skyblue', alpha=0.7)
        ax2.axhline(y=cv_scores.mean(), color='red', linestyle='--', label=f'Mean: {cv_scores.mean():.3f}')
        ax2.set_title('Cross-Validation Scores')
        ax2.set_xlabel('Fold')
        ax2.set_ylabel('Accuracy')
        ax2.legend()
        
        # Feature importance (from Random Forest)
        if hasattr(self.ensemble_model.named_estimators_['rf'], 'feature_importances_'):
            importances = self.ensemble_model.named_estimators_['rf'].feature_importances_
            indices = np.argsort(importances)[::-1][:10]
            ax3.bar(range(len(indices)), importances[indices])
            ax3.set_title('Top 10 Feature Importances')
            ax3.set_xlabel('Feature Index')
            ax3.set_ylabel('Importance')
        
        # Class distribution
        unique, counts = np.unique(self.label_encoder.classes_, return_counts=True)
        ax4.pie(counts, labels=unique, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Class Distribution')
        
        plt.tight_layout()
        plt.savefig('optimized_quantum_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📈 Results saved as 'optimized_quantum_results.png'")

def main():
    """Main optimized training pipeline."""
    print("⚡ Optimized Quantum ML for Radiological Detection")
    print("=" * 60)
    
    # Initialize optimized classifier
    opt_qml = OptimizedQuantumML()
    
    # Load data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    try:
        # Load and analyze
        df = opt_qml.load_and_analyze_data(csv_file)
        
        # Prepare optimized features
        X, y = opt_qml.prepare_optimized_data(df, sample_size=500)  # Use 500 files for better balance
        
        # Train optimized model
        results = opt_qml.train_optimized_model(X, y)
        
        print("\n🎯 Optimized Results Summary:")
        print(f"   - Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"   - Cross-Validation: {results['cv_mean']:.3f} ± {results['cv_std']:.3f}")
        print(f"   - Training Time: {results['training_time']}")
        
        if results['test_accuracy'] > 0.8:
            print("🎉 Excellent! Ready for quantum enhancement!")
        elif results['test_accuracy'] > 0.6:
            print("👍 Good baseline! Can be improved with quantum methods")
        else:
            print("⚠️ Need more feature engineering")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
