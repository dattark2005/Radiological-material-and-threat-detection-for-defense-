#!/usr/bin/env python3
"""
Data Analysis Script - Identify issues causing low accuracy
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def analyze_dataset_issues(csv_file):
    """Analyze the dataset to identify issues."""
    print("🔍 Analyzing Dataset Issues")
    print("=" * 40)
    
    # Load data
    df = pd.read_csv(csv_file)
    print(f"📊 Dataset Overview:")
    print(f"   - Total rows: {len(df):,}")
    print(f"   - Unique files: {df['File'].nunique()}")
    print(f"   - Columns: {list(df.columns)}")
    
    # 1. Class Distribution Analysis
    print("\n🎯 Class Distribution Analysis:")
    isotope_counts = df.groupby('Isotope')['File'].nunique().sort_values(ascending=False)
    print("   Files per isotope:")
    for isotope, count in isotope_counts.items():
        percentage = (count / df['File'].nunique()) * 100
        print(f"     {isotope}: {count} files ({percentage:.1f}%)")
    
    # 2. Data Quality Issues
    print("\n🔧 Data Quality Issues:")
    
    # Check for zero counts
    zero_counts = (df['Counts'] == 0).sum()
    print(f"   - Zero count entries: {zero_counts:,} ({zero_counts/len(df)*100:.1f}%)")
    
    # Check energy range
    print(f"   - Energy range: {df['Energy_keV'].min():.2f} - {df['Energy_keV'].max():.2f} keV")
    
    # Check for missing values
    missing_values = df.isnull().sum()
    if missing_values.sum() > 0:
        print("   - Missing values:")
        for col, count in missing_values.items():
            if count > 0:
                print(f"     {col}: {count}")
    else:
        print("   - No missing values ✅")
    
    # 3. Spectrum Analysis
    print("\n📈 Spectrum Analysis:")
    
    # Analyze spectrum lengths
    spectrum_lengths = df.groupby('File').size()
    print(f"   - Spectrum lengths: {spectrum_lengths.min()} - {spectrum_lengths.max()} channels")
    print(f"   - Average spectrum length: {spectrum_lengths.mean():.0f} channels")
    
    # Check for very short spectra
    short_spectra = (spectrum_lengths < 100).sum()
    if short_spectra > 0:
        print(f"   ⚠️ Short spectra (<100 channels): {short_spectra} files")
    
    # 4. Signal Quality Analysis
    print("\n📡 Signal Quality Analysis:")
    
    # Analyze count statistics per file
    file_stats = df.groupby('File')['Counts'].agg(['sum', 'max', 'mean', 'std']).reset_index()
    file_stats = file_stats.merge(df[['File', 'Isotope']].drop_duplicates(), on='File')
    
    print("   Count statistics by isotope:")
    isotope_stats = file_stats.groupby('Isotope')[['sum', 'max', 'mean']].mean()
    for isotope in isotope_stats.index:
        stats = isotope_stats.loc[isotope]
        print(f"     {isotope}: Total={stats['sum']:.0f}, Max={stats['max']:.0f}, Mean={stats['mean']:.2f}")
    
    # 5. Feature Separability Analysis
    print("\n🎯 Feature Separability Analysis:")
    
    # Calculate basic features per file
    features_per_file = []
    for file_name in df['File'].unique()[:100]:  # Sample first 100 files
        file_data = df[df['File'] == file_name]
        counts = file_data['Counts'].values
        energies = file_data['Energy_keV'].values
        
        if len(counts) > 0:
            features = {
                'file': file_name,
                'isotope': file_data['Isotope'].iloc[0],
                'total_counts': np.sum(counts),
                'max_counts': np.max(counts),
                'mean_energy': np.mean(energies),
                'peak_ratio': np.max(counts) / np.mean(counts) if np.mean(counts) > 0 else 0
            }
            features_per_file.append(features)
    
    feature_df = pd.DataFrame(features_per_file)
    
    # Check feature overlap between classes
    print("   Feature ranges by isotope (sample of 100 files):")
    for isotope in feature_df['isotope'].unique():
        isotope_data = feature_df[feature_df['isotope'] == isotope]
        if len(isotope_data) > 0:
            print(f"     {isotope} ({len(isotope_data)} files):")
            print(f"       Total counts: {isotope_data['total_counts'].min():.0f} - {isotope_data['total_counts'].max():.0f}")
            print(f"       Peak ratio: {isotope_data['peak_ratio'].min():.2f} - {isotope_data['peak_ratio'].max():.2f}")
    
    # 6. Recommendations
    print("\n💡 Recommendations to Improve Accuracy:")
    
    recommendations = []
    
    # Class imbalance
    class_imbalance = isotope_counts.max() / isotope_counts.min()
    if class_imbalance > 10:
        recommendations.append(f"🔄 Severe class imbalance (ratio: {class_imbalance:.1f}:1) - Use balanced sampling")
    
    # Zero counts
    if zero_counts > len(df) * 0.5:
        recommendations.append("🔧 Too many zero counts - Consider background subtraction")
    
    # Short spectra
    if short_spectra > 0:
        recommendations.append(f"📏 {short_spectra} short spectra - Filter out or pad")
    
    # Low signal
    low_signal_files = (file_stats['sum'] < 1000).sum()
    if low_signal_files > 0:
        recommendations.append(f"📡 {low_signal_files} low-signal files - Consider longer acquisition times")
    
    if not recommendations:
        recommendations.append("✅ Data quality looks good - Focus on feature engineering")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # 7. Create visualizations
    create_diagnostic_plots(df, feature_df)
    
    return {
        'isotope_counts': isotope_counts,
        'zero_counts_pct': zero_counts/len(df)*100,
        'class_imbalance_ratio': class_imbalance,
        'recommendations': recommendations
    }

def create_diagnostic_plots(df, feature_df):
    """Create diagnostic plots."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Class distribution
    isotope_counts = df.groupby('Isotope')['File'].nunique()
    ax1.bar(isotope_counts.index, isotope_counts.values, color='skyblue', alpha=0.7)
    ax1.set_title('Files per Isotope')
    ax1.set_xlabel('Isotope')
    ax1.set_ylabel('Number of Files')
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Count distribution
    df_sample = df.sample(n=min(10000, len(df)))  # Sample for performance
    ax2.hist(df_sample['Counts'], bins=50, alpha=0.7, color='green')
    ax2.set_title('Count Distribution (Sample)')
    ax2.set_xlabel('Counts')
    ax2.set_ylabel('Frequency')
    ax2.set_yscale('log')
    
    # 3. Energy vs Counts scatter
    ax3.scatter(df_sample['Energy_keV'], df_sample['Counts'], alpha=0.5, s=1)
    ax3.set_title('Energy vs Counts')
    ax3.set_xlabel('Energy (keV)')
    ax3.set_ylabel('Counts')
    
    # 4. Feature separability
    if len(feature_df) > 0:
        for isotope in feature_df['isotope'].unique():
            isotope_data = feature_df[feature_df['isotope'] == isotope]
            ax4.scatter(isotope_data['total_counts'], isotope_data['peak_ratio'], 
                       label=isotope, alpha=0.7)
        ax4.set_title('Feature Separability')
        ax4.set_xlabel('Total Counts')
        ax4.set_ylabel('Peak Ratio')
        ax4.legend()
        ax4.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig('data_analysis_diagnostics.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Diagnostic plots saved as 'data_analysis_diagnostics.png'")

def main():
    """Main analysis function."""
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    try:
        results = analyze_dataset_issues(csv_file)
        
        print(f"\n📋 Analysis Summary:")
        print(f"   - Class imbalance ratio: {results['class_imbalance_ratio']:.1f}:1")
        print(f"   - Zero counts: {results['zero_counts_pct']:.1f}%")
        print(f"   - Main issue: {'Class imbalance' if results['class_imbalance_ratio'] > 5 else 'Data quality'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
