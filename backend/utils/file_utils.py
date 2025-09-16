import os
import json
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    """Save uploaded file and return file info."""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{file_id}.{file_extension}"
        
        # Create upload path
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(upload_path)
        
        return {
            'filename': filename,
            'original_filename': file.filename,
            'file_path': upload_path,
            'file_size': os.path.getsize(upload_path),
            'file_type': file_extension
        }
    
    return None

def parse_spectrum_file(file_path, file_type):
    """Parse spectrum data from uploaded file."""
    try:
        if file_type == 'csv':
            return parse_csv_spectrum(file_path)
        elif file_type == 'json':
            return parse_json_spectrum(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        raise ValueError(f"Error parsing spectrum file: {str(e)}")

def parse_csv_spectrum(file_path):
    """Parse CSV spectrum file."""
    df = pd.read_csv(file_path)
    
    # Try to find energy and counts columns
    energy_col = None
    counts_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'energy' in col_lower and energy_col is None:
            energy_col = col
        elif 'count' in col_lower and counts_col is None:
            counts_col = col
    
    if energy_col is None or counts_col is None:
        raise ValueError("CSV must contain 'energy' and 'counts' columns")
    
    energy = df[energy_col].values.tolist()
    counts = df[counts_col].values.tolist()
    
    # Validate data
    if len(energy) != len(counts):
        raise ValueError("Energy and counts arrays must have the same length")
    
    if len(energy) == 0:
        raise ValueError("No data found in file")
    
    return {
        'energy': energy,
        'counts': counts,
        'energy_range_min': float(min(energy)),
        'energy_range_max': float(max(energy)),
        'total_counts': int(sum(counts)),
        'data_points': len(energy)
    }

def parse_json_spectrum(file_path):
    """Parse JSON spectrum file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'energy' not in data or 'counts' not in data:
        raise ValueError("JSON must contain 'energy' and 'counts' arrays")
    
    energy = data['energy']
    counts = data['counts']
    
    # Validate data
    if not isinstance(energy, list) or not isinstance(counts, list):
        raise ValueError("Energy and counts must be arrays")
    
    if len(energy) != len(counts):
        raise ValueError("Energy and counts arrays must have the same length")
    
    if len(energy) == 0:
        raise ValueError("No data found in file")
    
    return {
        'energy': energy,
        'counts': counts,
        'energy_range_min': float(min(energy)),
        'energy_range_max': float(max(energy)),
        'total_counts': int(sum(counts)),
        'data_points': len(energy)
    }

def generate_synthetic_spectrum(isotope, noise_level=1):
    """Generate synthetic gamma-ray spectrum."""
    isotope_data = {
        'K-40': {'peaks': [1460.8], 'intensities': [10.7], 'background': 50},
        'Cs-137': {'peaks': [661.7], 'intensities': [85.1], 'background': 30},
        'Co-60': {'peaks': [1173.2, 1332.5], 'intensities': [99.85, 99.98], 'background': 40},
        'U-238': {'peaks': [1001.0, 766.4], 'intensities': [0.84, 0.29], 'background': 60},
        'mixed': {'peaks': [661.7, 1460.8], 'intensities': [85.1, 10.7], 'background': 45}
    }
    
    if isotope not in isotope_data:
        raise ValueError(f"Unknown isotope: {isotope}")
    
    data = isotope_data[isotope]
    energy = list(range(0, 2001, 10))  # 0 to 2000 keV in 10 keV steps
    counts = []
    
    for e in energy:
        # Background noise
        count = np.random.poisson(data['background'] * noise_level)
        
        # Add peaks
        for peak_energy, intensity in zip(data['peaks'], data['intensities']):
            sigma = 20  # Peak width
            amplitude = intensity * 10 * (4 - noise_level)  # Adjust for noise
            gaussian = amplitude * np.exp(-((e - peak_energy) ** 2) / (2 * sigma ** 2))
            count += np.random.poisson(max(0, gaussian))
        
        counts.append(max(0, count))
    
    return {
        'energy': energy,
        'counts': counts,
        'energy_range_min': float(min(energy)),
        'energy_range_max': float(max(energy)),
        'total_counts': int(sum(counts)),
        'data_points': len(energy),
        'isotope': isotope,
        'noise_level': noise_level
    }

def validate_spectrum_data(spectrum_data):
    """Validate spectrum data structure and values."""
    required_fields = ['energy', 'counts']
    
    for field in required_fields:
        if field not in spectrum_data:
            raise ValueError(f"Missing required field: {field}")
    
    energy = spectrum_data['energy']
    counts = spectrum_data['counts']
    
    if not isinstance(energy, list) or not isinstance(counts, list):
        raise ValueError("Energy and counts must be lists")
    
    if len(energy) != len(counts):
        raise ValueError("Energy and counts must have the same length")
    
    if len(energy) == 0:
        raise ValueError("Spectrum data cannot be empty")
    
    # Check for valid numeric values
    try:
        energy = [float(e) for e in energy]
        counts = [float(c) for c in counts]
    except (ValueError, TypeError):
        raise ValueError("Energy and counts must contain numeric values")
    
    # Check for negative values
    if any(e < 0 for e in energy):
        raise ValueError("Energy values cannot be negative")
    
    if any(c < 0 for c in counts):
        raise ValueError("Count values cannot be negative")
    
    return True

def cleanup_old_files(max_age_days=7):
    """Clean up old uploaded files."""
    import time
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    deleted_count = 0
    
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getctime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError:
                    pass  # File might be in use
    
    return deleted_count
