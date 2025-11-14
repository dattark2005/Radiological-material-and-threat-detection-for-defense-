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
            
            # Generate XAI explanations
            xai_explanations = self._generate_xai_explanations(
                spectrum_data, classified_isotope, detected_peaks, confidence
            )
            
            return {
                'threat_probability': threat_probability,
                'classified_isotope': classified_isotope,
                'confidence_level': confidence_level,
                'material_quantity': material_quantity,
                'detected_peaks': detected_peaks,
                'model_confidence': confidence,
                'processing_time': processing_time,
                'xai_explanations': xai_explanations
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
    
    def _generate_xai_explanations(self, spectrum_data, classified_isotope, detected_peaks, confidence):
        """Generate explainable AI explanations for the analysis."""
        try:
            energy = np.array(spectrum_data['energy'])
            counts = np.array(spectrum_data['counts'])
            
            # Calculate feature importance based on actual analysis
            feature_importance = []
            
            # Peak-based features
            for peak in detected_peaks[:5]:  # Top 5 peaks
                importance_value = peak['significance'] * 0.001
                feature_importance.append({
                    'name': f"{peak['energy']:.1f} keV Peak",
                    'value': importance_value,
                    'positive': True,
                    'description': f"Peak intensity: {peak['intensity']:.2f}, significance: {peak['significance']:.3f}"
                })
            
            # Background noise feature
            background_level = np.mean(counts[:100])  # First 100 channels as background
            feature_importance.append({
                'name': 'Background Noise Level',
                'value': -background_level * 0.0001,
                'positive': False,
                'description': f"Background level: {background_level:.3f}"
            })
            
            # Spectrum quality feature
            max_count = np.max(counts)
            avg_count = np.mean(counts)
            snr = max_count / avg_count if avg_count > 0 else 0
            feature_importance.append({
                'name': 'Signal-to-Noise Ratio',
                'value': min(snr * 0.00005, 0.001),
                'positive': True,
                'description': f"SNR: {snr:.2f}"
            })
            
            # Count statistics feature
            total_counts = np.sum(counts)
            feature_importance.append({
                'name': 'Count Statistics',
                'value': min(total_counts / 1000000, 0.001),
                'positive': True,
                'description': f"Total counts: {total_counts:.0f}"
            })
            
            # Calculate uncertainty
            epistemic_uncertainty = max(5.0, (1.0 - confidence) * 20.0)
            aleatoric_uncertainty = max(3.0, background_level * 10.0)
            total_uncertainty = np.sqrt(epistemic_uncertainty**2 + aleatoric_uncertainty**2)
            
            # LIME-like local explanations
            lime_explanations = []
            if classified_isotope != 'Unknown':
                signature_peaks = self.isotope_signatures.get(classified_isotope, {}).get('peaks', [])
                for sig_peak in signature_peaks:
                    # Find closest detected peak
                    closest_peak = None
                    min_diff = float('inf')
                    for peak in detected_peaks:
                        diff = abs(peak['energy'] - sig_peak)
                        if diff < min_diff:
                            min_diff = diff
                            closest_peak = peak
                    
                    if closest_peak and min_diff < sig_peak * 0.05:  # Within 5% tolerance
                        lime_explanations.append({
                            'name': f'Energy Channel {sig_peak:.0f} keV',
                            'weight': closest_peak['significance'] * 0.001,
                            'desc': f"{classified_isotope} signature peak (intensity: {closest_peak['intensity']:.2f})",
                            'positive': True
                        })
            
            return {
                'feature_importance': feature_importance,
                'uncertainty': {
                    'total': min(total_uncertainty, 50.0),
                    'epistemic': min(epistemic_uncertainty, 30.0),
                    'aleatoric': min(aleatoric_uncertainty, 25.0)
                },
                'lime_explanations': lime_explanations,
                'model_prediction': {
                    'threatLevel': self._get_threat_level(classified_isotope),
                    'confidence': confidence * 100,
                    'isotope': classified_isotope,
                    'activity': self._estimate_activity_level(detected_peaks)
                }
            }
            
        except Exception as e:
            logging.error(f"XAI explanation generation error: {str(e)}")
            return {
                'feature_importance': [],
                'uncertainty': {'total': 15.0, 'epistemic': 10.0, 'aleatoric': 5.0},
                'lime_explanations': [],
                'model_prediction': {
                    'threatLevel': 'Unknown',
                    'confidence': 0.0,
                    'isotope': 'Unknown',
                    'activity': 'Unknown'
                }
            }
    
    def _get_threat_level(self, isotope):
        """Convert isotope to threat level."""
        if isotope == 'Unknown':
            return 'Low Risk'
        
        threat_prob = self.isotope_signatures.get(isotope, {}).get('threat_level', 0.1)
        if threat_prob >= 0.9:
            return 'Very High Risk'
        elif threat_prob >= 0.7:
            return 'High Risk'
        elif threat_prob >= 0.4:
            return 'Medium Risk'
        else:
            return 'Low Risk'
    
    def _estimate_activity_level(self, detected_peaks):
        """Estimate activity level based on peak characteristics."""
        if not detected_peaks:
            return 'Low'
        
        max_significance = max(peak['significance'] for peak in detected_peaks)
        if max_significance > 0.5:
            return 'High'
        elif max_significance > 0.2:
            return 'Medium'
        else:
            return 'Low'
