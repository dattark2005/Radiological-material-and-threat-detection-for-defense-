import os
import re
import pandas as pd
from tqdm import tqdm

# Folder containing your 1591 .spe files
SOURCE_DIR = "ieae_data"
OUTPUT_DIR = "converted_csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_spe(file_path):
    """Read .spe file and extract metadata, calibration, and counts"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Extract isotope or material info
    isotope_match = re.search(r"Material type:\s*(.*)", text)
    isotope = isotope_match.group(1).strip() if isotope_match else "Unknown"
    
    # Extract additional metadata
    detector_match = re.search(r"Detector:\s*(.*)", text)
    detector = detector_match.group(1).strip() if detector_match else "Unknown"
    
    date_match = re.search(r"\$DATE_MEA:\s*([^\n]+)", text)
    measurement_date = date_match.group(1).strip() if date_match else "Unknown"
    
    # Extract measurement time
    time_match = re.search(r"\$MEAS_TIM:\s*(\d+)\s+(\d+)", text)
    live_time, real_time = (0, 0)
    if time_match:
        live_time, real_time = map(int, time_match.groups())

    # Extract energy calibration (after $ENER_FIT:)
    calib_match = re.search(r"\$ENER_FIT:\s*\n([-\d\.E+]+)\s+([-\d\.E+]+)", text)
    intercept, slope = (0.0, 0.075)  # Default values
    if calib_match:
        intercept, slope = map(float, calib_match.groups())

    # Extract data block (between $DATA: and $ENER_FIT:)
    data_match = re.search(r"\$DATA:\s*\n(\d+)\s+(\d+)\s*\n([\s\S]*?)\$ENER_FIT:", text)
    if not data_match:
        print(f"No data block found in {file_path}")
        return None
    
    start_ch, end_ch, data_section = data_match.groups()
    start_ch, end_ch = int(start_ch), int(end_ch)
    
    # Parse counts data
    counts = []
    for line in data_section.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('$'):
            try:
                counts.append(int(line))
            except ValueError:
                continue
    
    # Generate channels and energies
    num_channels = len(counts)
    channels = list(range(start_ch, start_ch + num_channels))
    energies = [intercept + slope * ch for ch in channels]
    
    # Create DataFrame
    df = pd.DataFrame({
        "File": os.path.basename(file_path),
        "Isotope": isotope,
        "Detector": detector,
        "Measurement_Date": measurement_date,
        "Live_Time_sec": live_time,
        "Real_Time_sec": real_time,
        "Channel": channels,
        "Energy_keV": energies,
        "Counts": counts
    })
    
    return df


# Process all .spe files
all_dfs = []
failed_files = []

print(f"🔍 Found {len([f for f in os.listdir(SOURCE_DIR) if f.lower().endswith('.spe')])} SPE files")

for file in tqdm(os.listdir(SOURCE_DIR), desc="Converting SPE files"):
    if file.lower().endswith(".spe"):
        path = os.path.join(SOURCE_DIR, file)
        df = parse_spe(path)
        if df is not None and not df.empty:
            all_dfs.append(df)
        else:
            failed_files.append(file)

if all_dfs:
    # Merge all into one master dataset
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Save master file
    master_file = os.path.join(OUTPUT_DIR, "all_spectra_master.csv")
    final_df.to_csv(master_file, index=False)
    
    # Create summary statistics
    summary = {
        'Total_Files_Processed': len(all_dfs),
        'Total_Spectra_Points': len(final_df),
        'Unique_Isotopes': final_df['Isotope'].nunique(),
        'Isotope_Counts': final_df['Isotope'].value_counts().to_dict(),
        'Energy_Range_keV': f"{final_df['Energy_keV'].min():.2f} - {final_df['Energy_keV'].max():.2f}",
        'Failed_Files': len(failed_files)
    }
    
    # Save summary
    summary_file = os.path.join(OUTPUT_DIR, "conversion_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("SPE to CSV Conversion Summary\n")
        f.write("=" * 30 + "\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
        
        if failed_files:
            f.write("\nFailed Files:\n")
            for file in failed_files:
                f.write(f"  - {file}\n")
    
    print(f"✅ Successfully converted {len(all_dfs)} spectra")
    print(f"📊 Total data points: {len(final_df):,}")
    print(f"🎯 Unique isotopes: {final_df['Isotope'].nunique()}")
    print(f"📁 Saved to: {master_file}")
    print(f"📋 Summary saved to: {summary_file}")
    
    if failed_files:
        print(f"⚠️  Failed to process {len(failed_files)} files")
else:
    print("❌ No valid SPE files were processed!")
