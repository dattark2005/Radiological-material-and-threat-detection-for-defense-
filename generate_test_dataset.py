#!/usr/bin/env python3
"""
Generate synthetic radiological dataset for testing ML models
"""

import numpy as np
import pandas as pd
import os
from datetime import datetime

def generate_gamma_spectrum(isotope_type, energy_range=(0, 3000), num_channels=1024):
    """Generate a realistic gamma-ray spectrum for a given isotope."""
    
    # Define characteristic peaks for different isotopes
    isotope_peaks = {
        'U-235': [143.8, 163.4, 185.7, 205.3],
        'U-238': [63.3, 92.4, 742.8, 1001.0],
        'Pu-239': [129.3, 203.5, 345.0, 375.0, 413.7],
        'Pu-240': [160.3, 642.2, 687.0],
        'Cs-137': [661.7],
        'Co-60': [1173.2, 1332.5],
        'background': []  # No specific peaks
    }
    
    energy_channels = np.linspace(energy_range[0], energy_range[1], num_channels)
    counts = np.random.poisson(50, num_channels)  # Background noise
    
    # Add characteristic peaks
    if isotope_type in isotope_peaks:
        for peak_energy in isotope_peaks[isotope_type]:
            if energy_range[0] <= peak_energy <= energy_range[1]:
                # Find closest channel
                peak_channel = np.argmin(np.abs(energy_channels - peak_energy))
                
                # Add Gaussian peak
                sigma = 5  # Peak width
                peak_height = np.random.randint(500, 2000)
                
                for i in range(max(0, peak_channel-15), min(num_channels, peak_channel+15)):
                    gaussian = peak_height * np.exp(-0.5 * ((i - peak_channel) / sigma) ** 2)
                    counts[i] += int(gaussian)
    
    return energy_channels.tolist(), counts.tolist()

def create_synthetic_dataset(num_samples_per_isotope=50):
    """Create a comprehensive synthetic dataset."""
    
    print("[INFO] Generating synthetic radiological dataset...")
    
    # Define isotopes and their threat levels
    isotopes = {
        'U-235': 'high',
        'U-238': 'medium', 
        'Pu-239': 'high',
        'Pu-240': 'high',
        'Cs-137': 'medium',
        'Co-60': 'low',
        'background': 'benign'
    }
    
    dataset = []
    spectrum_id = 1
    
    for isotope, threat_level in isotopes.items():
        print(f"[INFO] Generating {num_samples_per_isotope} spectra for {isotope}...")
        
        for i in range(num_samples_per_isotope):
            # Generate spectrum
            energy_channels, counts = generate_gamma_spectrum(isotope)
            
            # Add some realistic variations
            live_time = np.random.uniform(300, 3600)  # 5 minutes to 1 hour
            total_counts = sum(counts)
            
            # Determine material type
            if 'U' in isotope:
                material_type = 'U'
            elif 'Pu' in isotope:
                material_type = 'Pu'
            elif isotope == 'background':
                material_type = 'background'
            else:
                material_type = 'other'
            
            spectrum_data = {
                'spectrum_id': f'synthetic_{spectrum_id:04d}',
                'source': 'synthetic',
                'energy_channels': str(energy_channels),  # Store as string for CSV
                'counts': str(counts),
                'isotope_label': isotope,
                'material_type': material_type,
                'threat_level': threat_level,
                'detector_type': np.random.choice(['NaI', 'HPGe', 'CZT']),
                'live_time': live_time,
                'total_counts': total_counts,
                'certificate_data': True,
                'data_quality': np.random.choice(['high', 'medium'], p=[0.8, 0.2])
            }
            
            dataset.append(spectrum_data)
            spectrum_id += 1
    
    return dataset

def extract_features_from_spectrum(energy_channels, counts):
    """Extract meaningful features from gamma-ray spectrum."""
    
    energy = np.array(eval(energy_channels))  # Convert string back to list
    counts_arr = np.array(eval(counts))
    
    features = {
        # Statistical features
        'total_counts': np.sum(counts_arr),
        'max_count': np.max(counts_arr),
        'mean_count': np.mean(counts_arr),
        'std_count': np.std(counts_arr),
        'skewness': float(np.mean(((counts_arr - np.mean(counts_arr)) / np.std(counts_arr)) ** 3)),
        
        # Energy features
        'energy_range': np.max(energy) - np.min(energy),
        'weighted_mean_energy': np.sum(energy * counts_arr) / np.sum(counts_arr),
        
        # Peak detection features
        'num_peaks': len([i for i in range(1, len(counts_arr)-1) 
                         if counts_arr[i] > counts_arr[i-1] and counts_arr[i] > counts_arr[i+1] 
                         and counts_arr[i] > np.mean(counts_arr) + 2*np.std(counts_arr)]),
        
        # Spectral shape features
        'low_energy_fraction': np.sum(counts_arr[:len(counts_arr)//3]) / np.sum(counts_arr),
        'mid_energy_fraction': np.sum(counts_arr[len(counts_arr)//3:2*len(counts_arr)//3]) / np.sum(counts_arr),
        'high_energy_fraction': np.sum(counts_arr[2*len(counts_arr)//3:]) / np.sum(counts_arr)
    }
    
    return features

def create_ml_ready_dataset(dataset):
    """Convert spectrum dataset to ML-ready format with extracted features."""
    
    print("[INFO] Extracting features for ML training...")
    
    ml_data = []
    
    for spectrum in dataset:
        # Extract features
        features = extract_features_from_spectrum(
            spectrum['energy_channels'], 
            spectrum['counts']
        )
        
        # Add metadata
        features.update({
            'spectrum_id': spectrum['spectrum_id'],
            'isotope_label': spectrum['isotope_label'],
            'material_type': spectrum['material_type'],
            'threat_level': spectrum['threat_level'],
            'detector_type': spectrum['detector_type'],
            'live_time': spectrum['live_time'],
            'data_quality': spectrum['data_quality']
        })
        
        ml_data.append(features)
    
    return pd.DataFrame(ml_data)

if __name__ == "__main__":
    # Create directories
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/raw', exist_ok=True)
    
    # Generate synthetic dataset
    dataset = create_synthetic_dataset(num_samples_per_isotope=30)
    
    # Save raw spectrum data
    df_raw = pd.DataFrame(dataset)
    raw_path = 'data/raw/synthetic_spectra.csv'
    df_raw.to_csv(raw_path, index=False)
    print(f"[SAVED] Raw synthetic spectra to {raw_path}")
    
    # Create ML-ready dataset
    df_ml = create_ml_ready_dataset(dataset)
    ml_path = 'data/processed/combined_dataset.csv'
    df_ml.to_csv(ml_path, index=False)
    print(f"[SAVED] ML-ready dataset to {ml_path}")
    
    # Print dataset summary
    print(f"\n[SUMMARY] Generated dataset:")
    print(f"  Total spectra: {len(dataset)}")
    print(f"  Isotope distribution:")
    for isotope in df_ml['isotope_label'].value_counts().items():
        print(f"    {isotope[0]}: {isotope[1]} spectra")
    
    print(f"  Threat level distribution:")
    for threat in df_ml['threat_level'].value_counts().items():
        print(f"    {threat[0]}: {threat[1]} spectra")
    
    print(f"  Feature columns: {len(df_ml.columns)}")
    print(f"  Features: {list(df_ml.select_dtypes(include=[np.number]).columns)}")
    
    print(f"\n[SUCCESS] Synthetic dataset ready for ML training!")
    print(f"[NEXT] Run: python backend/training/classical_trainer.py --data {ml_path}")
    print(f"[NEXT] Run: python backend/training/quantum_trainer.py --data {ml_path}")
