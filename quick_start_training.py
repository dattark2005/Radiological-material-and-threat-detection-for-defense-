#!/usr/bin/env python3
"""
Quick Start Script for Model Training
Run this to begin training your radiological threat detection models
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

def setup_directories():
    """Create necessary directories for training."""
    directories = [
        'data/raw',
        'data/processed', 
        'data/synthetic',
        'data/validation',
        'ml_models/classical',
        'ml_models/quantum',
        'training/logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install required packages for training."""
    packages = [
        'scikit-learn>=1.3.0',
        'pandas>=1.5.0',
        'numpy>=1.24.0',
        'matplotlib>=3.6.0',
        'seaborn>=0.12.0',
        'shap>=0.42.0',
        'lime>=0.2.0',
        'qiskit>=0.44.0',
        'qiskit-machine-learning>=0.7.0',
        'joblib>=1.3.0',
        'scipy>=1.10.0'
    ]
    
    print("📦 Installing ML training dependencies...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")

def generate_sample_dataset():
    """Generate a sample dataset for initial training."""
    print("🔬 Generating sample radiological dataset...")
    
    # Isotope configurations
    isotopes = {
        'Cs-137': {'peaks': [661.7], 'threat_level': 'high'},
        'Co-60': {'peaks': [1173.2, 1332.5], 'threat_level': 'medium'},
        'K-40': {'peaks': [1460.8], 'threat_level': 'benign'},
        'U-238': {'peaks': [1001.0, 766.4], 'threat_level': 'high'},
        'background': {'peaks': [], 'threat_level': 'benign'}
    }
    
    dataset = []
    spectrum_id = 0
    
    for isotope, config in isotopes.items():
        for sample in range(200):  # 200 samples per isotope
            spectrum_id += 1
            
            # Generate energy channels (0-3000 keV)
            energy_channels = list(range(0, 3001, 10))
            
            # Generate spectrum with peaks
            counts = np.random.poisson(50, len(energy_channels))  # Background
            
            for peak_energy in config['peaks']:
                peak_idx = int(peak_energy / 10)  # Convert keV to index
                if peak_idx < len(counts):
                    # Add Gaussian peak
                    sigma = 5  # Peak width
                    for i in range(max(0, peak_idx-15), min(len(counts), peak_idx+15)):
                        gaussian = 1000 * np.exp(-((i - peak_idx) ** 2) / (2 * sigma ** 2))
                        counts[i] += int(np.random.poisson(gaussian))
            
            # Add noise
            noise_level = np.random.randint(1, 4)
            counts = counts + np.random.poisson(10 * noise_level, len(counts))
            counts = np.maximum(counts, 0)  # Ensure non-negative
            
            dataset.append({
                'spectrum_id': f'sample_{spectrum_id:04d}',
                'energy_channels': energy_channels,
                'counts': counts.tolist(),
                'isotope_label': isotope,
                'threat_level': config['threat_level'],
                'activity_bq': np.random.randint(100, 10000),
                'measurement_time': 300,
                'detector_type': np.random.choice(['NaI', 'HPGe', 'CZT']),
                'shielding': np.random.choice(['none', 'lead', 'concrete']),
                'distance_m': np.random.uniform(0.5, 5.0),
                'background_subtracted': True
            })
    
    # Save dataset
    df = pd.DataFrame(dataset)
    df.to_csv('data/processed/sample_radiological_dataset.csv', index=False)
    print(f"✅ Generated {len(dataset)} sample spectra")
    print(f"📁 Saved to: data/processed/sample_radiological_dataset.csv")
    
    return df

def run_initial_training():
    """Run initial model training."""
    print("🤖 Starting initial model training...")
    
    try:
        # Import training modules
        sys.path.append('backend/training')
        from classical_trainer import ClassicalModelTrainer
        
        # Load sample dataset
        df = pd.read_csv('data/processed/sample_radiological_dataset.csv')
        
        # Initialize trainer
        trainer = ClassicalModelTrainer()
        
        # Extract features (simplified for demo)
        print("🔍 Extracting features...")
        X = []
        y = []
        
        for _, row in df.iterrows():
            counts = eval(row['counts'])  # Convert string back to list
            
            # Simple feature extraction
            features = [
                sum(counts),  # total_counts
                max(counts),  # max_count
                np.mean(counts),  # mean_count
                np.std(counts),  # std_count
                len([c for c in counts if c > np.mean(counts) + 2*np.std(counts)]),  # num_peaks
                row['activity_bq'],
                row['distance_m']
            ]
            
            X.append(features)
            y.append(row['threat_level'])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"📊 Dataset shape: {X.shape}")
        print(f"📊 Classes: {np.unique(y)}")
        
        # Train models
        trainer.feature_names = [
            'total_counts', 'max_count', 'mean_count', 'std_count', 
            'num_peaks', 'activity_bq', 'distance_m'
        ]
        
        X_test, y_test = trainer.train_models(X, y)
        trainer.save_models('ml_models/classical')
        trainer.generate_report()
        
        print("✅ Initial training completed!")
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        print("💡 You can still proceed with manual training using the generated dataset")

def create_training_notebook():
    """Create a Jupyter notebook for interactive training."""
    notebook_content = '''
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Radiological Threat Detection - Model Training\\n",
    "\\n",
    "This notebook guides you through training classical and quantum ML models for radiological threat detection."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "from sklearn.model_selection import train_test_split\\n",
    "from sklearn.ensemble import RandomForestClassifier\\n",
    "from sklearn.metrics import classification_report\\n",
    "\\n",
    "# Load dataset\\n",
    "df = pd.read_csv('data/processed/sample_radiological_dataset.csv')\\n",
    "print(f'Dataset shape: {df.shape}')\\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Feature Extraction\\n",
    "Extract meaningful features from gamma-ray spectra"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "# Feature extraction code here\\n",
    "# See backend/training/classical_trainer.py for complete implementation"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
'''
    
    with open('training_notebook.ipynb', 'w') as f:
        f.write(notebook_content)
    
    print("📓 Created training_notebook.ipynb for interactive development")

def main():
    """Main setup function."""
    print("🚀 QUANTUM ML RADIOLOGICAL THREAT DETECTION")
    print("=" * 50)
    print("Setting up training environment...")
    print()
    
    # Setup
    setup_directories()
    print()
    
    # Install dependencies
    install_dependencies()
    print()
    
    # Generate sample data
    generate_sample_dataset()
    print()
    
    # Create notebook
    create_training_notebook()
    print()
    
    # Run initial training
    run_initial_training()
    print()
    
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("Next steps:")
    print("1. 📊 Review the generated sample dataset in data/processed/")
    print("2. 🤖 Check trained models in ml_models/classical/")
    print("3. 📓 Open training_notebook.ipynb for interactive development")
    print("4. 🔬 Collect real radiological datasets (IAEA, NIST)")
    print("5. 🚀 Train production models with real data")
    print()
    print("For quantum training:")
    print("   python backend/training/quantum_trainer.py")
    print()
    print("For explainable AI:")
    print("   python backend/services/explainable_ai_service.py")

if __name__ == "__main__":
    main()
