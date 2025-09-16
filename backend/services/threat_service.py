import numpy as np
import logging
from datetime import datetime

class ThreatAssessmentService:
    """Service for comprehensive threat assessment and risk analysis."""
    
    def __init__(self):
        self.threat_thresholds = {
            'clear': 0.5,
            'warning': 0.8
        }
        
        self.isotope_risk_factors = {
            'K-40': {'risk_multiplier': 0.1, 'contamination_factor': 1.0},
            'Cs-137': {'risk_multiplier': 0.8, 'contamination_factor': 3.0},
            'Co-60': {'risk_multiplier': 0.9, 'contamination_factor': 2.5},
            'U-238': {'risk_multiplier': 0.95, 'contamination_factor': 5.0},
            'Ra-226': {'risk_multiplier': 0.85, 'contamination_factor': 4.0},
            'Am-241': {'risk_multiplier': 0.9, 'contamination_factor': 3.5}
        }
        
        self.quantity_multipliers = {
            'Small': 1.0,
            'Medium': 2.0,
            'Large': 4.0
        }
    
    def assess_threat(self, ml_results):
        """Perform comprehensive threat assessment from ML results."""
        try:
            if not ml_results:
                return self._create_default_assessment()
            
            # Extract results from different models
            classical_result = None
            quantum_result = None
            
            for result in ml_results:
                if isinstance(result, dict):
                    # Direct result dictionary
                    if 'model_type' in result:
                        if result['model_type'] == 'classical':
                            classical_result = result
                        elif result['model_type'] == 'quantum':
                            quantum_result = result
                    else:
                        # Assume it's a classical result if no type specified
                        classical_result = result
            
            # If we don't have separate model results, treat the first as classical
            if not classical_result and not quantum_result and ml_results:
                classical_result = ml_results[0]
            
            # Calculate consensus threat probability
            threat_probabilities = []
            isotopes = []
            quantities = []
            
            if classical_result:
                threat_probabilities.append(classical_result.get('threat_probability', 0.0))
                isotopes.append(classical_result.get('classified_isotope', 'Unknown'))
                quantities.append(classical_result.get('material_quantity', 'Small'))
            
            if quantum_result:
                threat_probabilities.append(quantum_result.get('threat_probability', 0.0))
                isotopes.append(quantum_result.get('classified_isotope', 'Unknown'))
                quantities.append(quantum_result.get('material_quantity', 'Small'))
            
            # Calculate overall threat probability
            overall_threat_probability = np.mean(threat_probabilities) if threat_probabilities else 0.0
            
            # Determine consensus isotope
            consensus_isotope = self._determine_consensus_isotope(isotopes)
            
            # Determine consensus quantity
            consensus_quantity = self._determine_consensus_quantity(quantities)
            
            # Calculate model agreement
            model_agreement = self._calculate_model_agreement(threat_probabilities, isotopes)
            
            # Determine threat level
            threat_level = self._determine_threat_level(overall_threat_probability)
            
            # Calculate contamination radius
            contamination_radius = self._calculate_contamination_radius(
                consensus_isotope, consensus_quantity, overall_threat_probability
            )
            
            # Determine emergency response level
            emergency_response_level = self._determine_emergency_response_level(
                threat_level, overall_threat_probability, consensus_isotope
            )
            
            # Check if evacuation is recommended
            evacuation_recommended = self._should_recommend_evacuation(
                threat_level, contamination_radius, consensus_isotope
            )
            
            return {
                'threat_level': threat_level,
                'overall_threat_probability': float(overall_threat_probability),
                'consensus_isotope': consensus_isotope,
                'contamination_radius': float(contamination_radius),
                'evacuation_recommended': evacuation_recommended,
                'emergency_response_level': emergency_response_level,
                'model_agreement': float(model_agreement),
                'assessment_details': {
                    'classical_threat': classical_result.get('threat_probability', 0.0) if classical_result else None,
                    'quantum_threat': quantum_result.get('threat_probability', 0.0) if quantum_result else None,
                    'consensus_quantity': consensus_quantity,
                    'risk_factors': self._get_risk_factors(consensus_isotope)
                }
            }
            
        except Exception as e:
            logging.error(f"Threat assessment error: {str(e)}")
            return self._create_default_assessment()
    
    def _create_default_assessment(self):
        """Create default safe assessment."""
        return {
            'threat_level': 'clear',
            'overall_threat_probability': 0.0,
            'consensus_isotope': 'Unknown',
            'contamination_radius': 0.0,
            'evacuation_recommended': False,
            'emergency_response_level': 0,
            'model_agreement': 1.0,
            'assessment_details': {
                'classical_threat': None,
                'quantum_threat': None,
                'consensus_quantity': 'Small',
                'risk_factors': {}
            }
        }
    
    def _determine_consensus_isotope(self, isotopes):
        """Determine consensus isotope from multiple model results."""
        if not isotopes:
            return 'Unknown'
        
        # Remove None and 'Unknown' values
        valid_isotopes = [iso for iso in isotopes if iso and iso != 'Unknown']
        
        if not valid_isotopes:
            return 'Unknown'
        
        # If all models agree, return that isotope
        if len(set(valid_isotopes)) == 1:
            return valid_isotopes[0]
        
        # If models disagree, return the most dangerous one
        threat_levels = {}
        for isotope in valid_isotopes:
            if isotope in self.isotope_risk_factors:
                threat_levels[isotope] = self.isotope_risk_factors[isotope]['risk_multiplier']
            else:
                threat_levels[isotope] = 0.5  # Default moderate threat
        
        return max(threat_levels.keys(), key=lambda x: threat_levels[x])
    
    def _determine_consensus_quantity(self, quantities):
        """Determine consensus material quantity."""
        if not quantities:
            return 'Small'
        
        # Remove None values
        valid_quantities = [q for q in quantities if q]
        
        if not valid_quantities:
            return 'Small'
        
        # Return the largest quantity (most conservative approach)
        quantity_order = {'Small': 1, 'Medium': 2, 'Large': 3}
        max_quantity = max(valid_quantities, key=lambda x: quantity_order.get(x, 1))
        
        return max_quantity
    
    def _calculate_model_agreement(self, threat_probabilities, isotopes):
        """Calculate agreement between different models."""
        if len(threat_probabilities) < 2:
            return 1.0
        
        # Calculate probability agreement
        prob_std = np.std(threat_probabilities)
        prob_agreement = max(0.0, 1.0 - (prob_std * 2))  # Normalize standard deviation
        
        # Calculate isotope agreement
        valid_isotopes = [iso for iso in isotopes if iso and iso != 'Unknown']
        if len(valid_isotopes) < 2:
            isotope_agreement = 1.0
        else:
            isotope_agreement = 1.0 if len(set(valid_isotopes)) == 1 else 0.5
        
        # Combined agreement score
        return (prob_agreement + isotope_agreement) / 2
    
    def _determine_threat_level(self, threat_probability):
        """Determine categorical threat level from probability."""
        if threat_probability >= self.threat_thresholds['warning']:
            return 'danger'
        elif threat_probability >= self.threat_thresholds['clear']:
            return 'warning'
        else:
            return 'clear'
    
    def _calculate_contamination_radius(self, isotope, quantity, threat_probability):
        """Calculate estimated contamination radius in meters."""
        base_radius = 10.0  # Base radius in meters
        
        # Isotope-specific contamination factor
        if isotope in self.isotope_risk_factors:
            contamination_factor = self.isotope_risk_factors[isotope]['contamination_factor']
        else:
            contamination_factor = 2.0  # Default moderate contamination
        
        # Quantity multiplier
        quantity_multiplier = self.quantity_multipliers.get(quantity, 1.0)
        
        # Threat probability multiplier
        threat_multiplier = 1.0 + (threat_probability * 2.0)
        
        # Calculate final radius
        radius = base_radius * contamination_factor * quantity_multiplier * threat_multiplier
        
        # Cap maximum radius at 1000 meters
        return min(radius, 1000.0)
    
    def _determine_emergency_response_level(self, threat_level, threat_probability, isotope):
        """Determine emergency response level (0-5 scale)."""
        if threat_level == 'clear':
            return 0
        elif threat_level == 'warning':
            return 2 if threat_probability > 0.6 else 1
        else:  # danger
            # High-risk isotopes get higher response levels
            high_risk_isotopes = ['U-238', 'Co-60', 'Am-241']
            if isotope in high_risk_isotopes:
                return 5 if threat_probability > 0.9 else 4
            else:
                return 4 if threat_probability > 0.9 else 3
    
    def _should_recommend_evacuation(self, threat_level, contamination_radius, isotope):
        """Determine if evacuation should be recommended."""
        if threat_level != 'danger':
            return False
        
        # Recommend evacuation for large contamination areas
        if contamination_radius > 100.0:
            return True
        
        # Recommend evacuation for highly dangerous isotopes
        high_danger_isotopes = ['U-238', 'Co-60', 'Am-241', 'Ra-226']
        if isotope in high_danger_isotopes and contamination_radius > 50.0:
            return True
        
        return False
    
    def _get_risk_factors(self, isotope):
        """Get risk factors for the given isotope."""
        if isotope in self.isotope_risk_factors:
            return self.isotope_risk_factors[isotope]
        else:
            return {'risk_multiplier': 0.5, 'contamination_factor': 2.0}
    
    def generate_threat_summary(self, assessment):
        """Generate human-readable threat summary."""
        threat_level = assessment['threat_level']
        probability = assessment['overall_threat_probability']
        isotope = assessment['consensus_isotope']
        
        if threat_level == 'clear':
            summary = f"No significant threat detected. Probability: {probability:.1%}"
        elif threat_level == 'warning':
            summary = f"Potential threat detected. {isotope} identified with {probability:.1%} confidence. Manual inspection recommended."
        else:  # danger
            summary = f"HIGH ALERT: Significant threat detected. {isotope} identified with {probability:.1%} confidence. Immediate response required."
        
        if assessment['evacuation_recommended']:
            summary += " EVACUATION RECOMMENDED."
        
        return summary
    
    def get_response_recommendations(self, assessment):
        """Get specific response recommendations based on assessment."""
        recommendations = []
        
        threat_level = assessment['threat_level']
        isotope = assessment['consensus_isotope']
        radius = assessment['contamination_radius']
        
        if threat_level == 'clear':
            recommendations.append("Continue normal operations")
            recommendations.append("Maintain regular monitoring schedule")
        
        elif threat_level == 'warning':
            recommendations.append("Increase monitoring frequency")
            recommendations.append("Deploy additional detection equipment")
            recommendations.append("Notify security personnel")
            recommendations.append("Prepare for potential escalation")
        
        else:  # danger
            recommendations.append("Immediately secure the area")
            recommendations.append(f"Establish {radius:.0f}m safety perimeter")
            recommendations.append("Contact radiation safety officer")
            recommendations.append("Deploy specialized response team")
            
            if assessment['evacuation_recommended']:
                recommendations.append("Begin evacuation procedures")
                recommendations.append("Notify emergency services")
            
            if isotope in ['U-238', 'Co-60']:
                recommendations.append("Contact nuclear regulatory authority")
                recommendations.append("Implement HAZMAT protocols")
        
        return recommendations
