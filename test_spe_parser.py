import os
import re
import pandas as pd

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
    
    print(f"File: {os.path.basename(file_path)}")
    print(f"Isotope: {isotope}")
    print(f"Detector: {detector}")
    print(f"Date: {measurement_date}")
    print(f"Live/Real time: {live_time}/{real_time} sec")
    print(f"Energy calibration: {intercept} + {slope} * channel")
    print(f"Channels: {start_ch} to {start_ch + num_channels - 1} ({num_channels} total)")
    print(f"Energy range: {energies[0]:.2f} to {energies[-1]:.2f} keV")
    print(f"Total counts: {sum(counts):,}")
    print(f"Max counts: {max(counts) if counts else 0}")
    print("-" * 50)
    
    return {
        'file': os.path.basename(file_path),
        'isotope': isotope,
        'detector': detector,
        'channels': num_channels,
        'total_counts': sum(counts),
        'energy_range': f"{energies[0]:.2f}-{energies[-1]:.2f} keV"
    }

# Test on first few files
test_files = ['1.spe', '2.spe', '25.spe', '100.spe', '1000.spe']
results = []

for file in test_files:
    file_path = os.path.join('ieae_data', file)
    if os.path.exists(file_path):
        result = parse_spe(file_path)
        if result:
            results.append(result)

print("\n📊 SUMMARY:")
print("=" * 50)
for result in results:
    print(f"{result['file']}: {result['isotope']} | {result['channels']} channels | {result['total_counts']:,} counts | {result['energy_range']}")
