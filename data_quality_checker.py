
def check_spectrum_quality(spectrum_data):
    '''Check if IAEA spectrum meets quality criteria.'''
    
    quality_score = 0
    issues = []
    
    # Check total counts
    total_counts = sum(spectrum_data['counts'])
    if total_counts > 100000:
        quality_score += 25
    elif total_counts > 50000:
        quality_score += 15
        issues.append("Low count statistics")
    else:
        issues.append("Very low count statistics")
    
    # Check energy range
    energy_range = max(spectrum_data['energy_channels']) - min(spectrum_data['energy_channels'])
    if energy_range > 2000:  # keV
        quality_score += 25
    elif energy_range > 1000:
        quality_score += 15
        issues.append("Limited energy range")
    else:
        issues.append("Very limited energy range")
    
    # Check for certificate data
    if spectrum_data.get('certificate_data', False):
        quality_score += 25
    else:
        issues.append("No certificate data")
    
    # Check detector type
    if spectrum_data.get('detector_type') in ['NaI', 'HPGe']:
        quality_score += 25
    else:
        issues.append("Unknown detector type")
    
    return {
        'quality_score': quality_score,
        'quality_grade': 'High' if quality_score >= 75 else 'Medium' if quality_score >= 50 else 'Low',
        'issues': issues,
        'usable': quality_score >= 40
    }
