import numpy as np
import time
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
import logging

class ClassicalMLService:
    """Classical ML service for spectrum analysis."""
    
    def __init__(self):
        self.isotope_signatures = {
            'K-40': {'peaks': [1460.8], 'threat_level': 0.1},
            'Cs-137': {'peaks': [661.7], 'threat_level': 0.8},
            'Co-60': {'peaks': [1173.2, 1332.5], 'threat_level': 0.9},
            'U-238': {'peaks': [1001.0, 766.4], 'threat_level': 0.95},
            'Ra-226': {'peaks': [186.2, 609.3], 'threat_level': 0.85},
            'Am-241': {'peaks': [59.5, 26.3], 'threat_level': 0.9}
        }
        
    def analyze(self, spectrum_data):
        """Perform classical ML analysis on spectrum data."""
        start_time = time.time()
        
        try:
            energy = np.array(spectrum_data['energy'])
            counts = np.array(spectrum_data['counts'])
            
            # Detect peaks
            detected_peaks = self._detect_peaks(energy, counts)
            
            # Classify isotope
            classified_isotope, confidence = self._classify_isotope(detected_peaks)
            
            # Calculate threat probability
            threat_probability = self._calculate_threat_probability(
                classified_isotope, detected_peaks, counts
            )
            
            # Determine confidence level and material quantity
            confidence_level = self._get_confidence_level(confidence)
            material_quantity = self._estimate_material_quantity(detected_peaks, counts)
            
            processing_time = time.time() - start_time
            
            return {
                'threat_probability': threat_probability,
                'classified_isotope': classified_isotope,
                'confidence_level': confidence_level,
                'material_quantity': material_quantity,
                'detected_peaks': detected_peaks,
                'model_confidence': confidence,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logging.error(f"Classical ML analysis error: {str(e)}")
            raise
    
    def _detect_peaks(self, energy, counts):
        """Detect significant peaks in the spectrum."""
        # Smooth the data
        from scipy.ndimage import gaussian_filter1d
        smoothed_counts = gaussian_filter1d(counts, sigma=2)
        
        # Find peaks
        peaks, properties = find_peaks(
            smoothed_counts,
            height=np.max(smoothed_counts) * 0.1,  # At least 10% of max
            distance=5,  # Minimum distance between peaks
            prominence=np.max(smoothed_counts) * 0.05
        )
        
        detected_peaks = []
        for peak_idx in peaks:
            peak_energy = energy[peak_idx]
            peak_intensity = counts[peak_idx]
            peak_significance = peak_intensity / np.max(counts)
            
            detected_peaks.append({
                'energy': float(peak_energy),
                'intensity': float(peak_intensity),
                'significance': float(peak_significance)
            })
        
        # Sort by significance
        detected_peaks.sort(key=lambda x: x['significance'], reverse=True)
        
        return detected_peaks[:10]  # Return top 10 peaks
    
    def _classify_isotope(self, detected_peaks):
        """Classify isotope based on detected peaks."""
        if not detected_peaks:
            return 'Unknown', 0.0
        
        best_match = 'Unknown'
        best_score = 0.0
        
        for isotope, signature in self.isotope_signatures.items():
            score = self._calculate_match_score(detected_peaks, signature['peaks'])
            if score > best_score:
                best_score = score
                best_match = isotope
        
        # Require minimum confidence for classification
        if best_score < 0.3:
            return 'Unknown', best_score
        
        return best_match, best_score
    
    def _calculate_match_score(self, detected_peaks, reference_peaks):
        """Calculate how well detected peaks match reference peaks."""
        if not detected_peaks or not reference_peaks:
            return 0.0
        
        total_score = 0.0
        matched_peaks = 0
        
        for ref_peak in reference_peaks:
            best_match_score = 0.0
            
            for detected_peak in detected_peaks:
                energy_diff = abs(detected_peak['energy'] - ref_peak)
                
                # Allow 5% energy tolerance
                tolerance = ref_peak * 0.05
                
                if energy_diff <= tolerance:
                    # Score based on energy match and peak significance
                    energy_score = 1.0 - (energy_diff / tolerance)
                    significance_score = detected_peak['significance']
                    match_score = energy_score * significance_score
                    
                    best_match_score = max(best_match_score, match_score)
            
            if best_match_score > 0:
                total_score += best_match_score
                matched_peaks += 1
        
        # Normalize by number of reference peaks
        if len(reference_peaks) > 0:
            return total_score / len(reference_peaks)
        
        return 0.0
    
    def _calculate_threat_probability(self, isotope, detected_peaks, counts):
        """Calculate threat probability based on isotope and peak characteristics."""
        base_threat = 0.1  # Background threat level
        
        if isotope in self.isotope_signatures:
            base_threat = self.isotope_signatures[isotope]['threat_level']
        
        # Adjust based on peak intensity
        if detected_peaks:
            max_significance = max(peak['significance'] for peak in detected_peaks)
            intensity_multiplier = 0.5 + (max_significance * 0.5)
            base_threat *= intensity_multiplier
        
        # Add some randomness for realism
        noise = np.random.normal(0, 0.05)
        threat_probability = np.clip(base_threat + noise, 0.0, 1.0)
        
        return float(threat_probability)
    
    def _get_confidence_level(self, confidence):
        """Convert numerical confidence to categorical level."""
        if confidence >= 0.8:
            return 'High'
        elif confidence >= 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_material_quantity(self, detected_peaks, counts):
        """Estimate material quantity based on peak characteristics."""
        if not detected_peaks:
            return 'Small'
        
        max_intensity = max(peak['intensity'] for peak in detected_peaks)
        total_counts = np.sum(counts)
        
        # Normalize by spectrum length
        normalized_intensity = max_intensity / len(counts)
        
        if normalized_intensity > 100:
            return 'Large'
        elif normalized_intensity > 50:
            return 'Medium'
        else:
            return 'Small'
