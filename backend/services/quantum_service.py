import numpy as np
import time
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import SamplerV2 as Sampler
import logging

class QuantumMLService:
    """Quantum ML service for spectrum analysis using VQC/QNN."""
    
    def __init__(self):
        self.backend = AerSimulator()
        self.num_qubits = 4
        self.num_layers = 3
        
        # Isotope quantum signatures (simulated)
        self.quantum_signatures = {
            'K-40': {'phase_pattern': [0.1, 0.3, 0.2, 0.4], 'threat_level': 0.15},
            'Cs-137': {'phase_pattern': [0.8, 0.6, 0.9, 0.7], 'threat_level': 0.85},
            'Co-60': {'phase_pattern': [0.9, 0.8, 0.95, 0.85], 'threat_level': 0.92},
            'U-238': {'phase_pattern': [0.95, 0.9, 0.98, 0.88], 'threat_level': 0.97},
            'Ra-226': {'phase_pattern': [0.85, 0.75, 0.9, 0.8], 'threat_level': 0.88},
            'Am-241': {'phase_pattern': [0.9, 0.85, 0.92, 0.87], 'threat_level': 0.91}
        }
        
    def analyze(self, spectrum_data):
        """Perform quantum ML analysis on spectrum data."""
        start_time = time.time()
        
        try:
            energy = np.array(spectrum_data['energy'])
            counts = np.array(spectrum_data['counts'])
            
            # Encode spectrum data into quantum features
            quantum_features = self._encode_spectrum_data(energy, counts)
            
            # Create and execute quantum circuit
            circuit = self._create_vqc_circuit(quantum_features)
            measurement_results = self._execute_quantum_circuit(circuit)
            
            # Decode quantum results
            classified_isotope, confidence = self._decode_quantum_results(measurement_results)
            
            # Calculate threat probability using quantum approach
            threat_probability = self._quantum_threat_assessment(
                measurement_results, classified_isotope
            )
            
            # Detect peaks using quantum-enhanced method
            detected_peaks = self._quantum_peak_detection(energy, counts)
            
            # Determine confidence level and material quantity
            confidence_level = self._get_confidence_level(confidence)
            material_quantity = self._quantum_quantity_estimation(measurement_results)
            
            processing_time = time.time() - start_time
            
            return {
                'threat_probability': threat_probability,
                'classified_isotope': classified_isotope,
                'confidence_level': confidence_level,
                'material_quantity': material_quantity,
                'detected_peaks': detected_peaks,
                'model_confidence': confidence,
                'processing_time': processing_time,
                'quantum_state': measurement_results
            }
            
        except Exception as e:
            logging.error(f"Quantum ML analysis error: {str(e)}")
            raise
    
    def _encode_spectrum_data(self, energy, counts):
        """Encode spectrum data into quantum features."""
        # Normalize and compress spectrum data
        normalized_counts = counts / np.max(counts) if np.max(counts) > 0 else counts
        
        # Extract key features for quantum encoding
        features = []
        
        # Energy distribution features
        energy_bins = np.linspace(0, 2000, self.num_qubits)
        for i in range(self.num_qubits):
            bin_start = energy_bins[i]
            bin_end = energy_bins[i + 1] if i < len(energy_bins) - 1 else 2000
            
            # Sum counts in this energy bin
            mask = (energy >= bin_start) & (energy < bin_end)
            bin_counts = np.sum(normalized_counts[mask])
            features.append(bin_counts)
        
        # Normalize features to [0, π] for quantum phases
        features = np.array(features)
        if np.max(features) > 0:
            features = (features / np.max(features)) * np.pi
        
        return features
    
    def _create_vqc_circuit(self, features):
        """Create Variational Quantum Classifier circuit."""
        qreg = QuantumRegister(self.num_qubits, 'q')
        creg = ClassicalRegister(self.num_qubits, 'c')
        circuit = QuantumCircuit(qreg, creg)
        
        # Data encoding layer
        for i, feature in enumerate(features):
            circuit.ry(feature, qreg[i])
        
        # Variational layers
        for layer in range(self.num_layers):
            # Entangling gates
            for i in range(self.num_qubits - 1):
                circuit.cx(qreg[i], qreg[i + 1])
            
            # Parameterized rotation gates
            for i in range(self.num_qubits):
                # Simulate trained parameters
                theta = np.random.uniform(0, 2 * np.pi)
                phi = np.random.uniform(0, 2 * np.pi)
                circuit.ry(theta, qreg[i])
                circuit.rz(phi, qreg[i])
        
        # Measurement
        circuit.measure(qreg, creg)
        
        return circuit
    
    def _execute_quantum_circuit(self, circuit):
        """Execute quantum circuit and return measurement results."""
        # Simulate quantum execution
        job = self.backend.run(circuit, shots=1024)
        result = job.result()
        counts = result.get_counts()
        
        # Convert to probability distribution
        total_shots = sum(counts.values())
        probabilities = {}
        
        for bitstring, count in counts.items():
            probabilities[bitstring] = count / total_shots
        
        return probabilities
    
    def _decode_quantum_results(self, measurement_results):
        """Decode quantum measurement results to classify isotope."""
        # Calculate quantum state vector representation
        state_vector = self._calculate_state_vector(measurement_results)
        
        best_match = 'Unknown'
        best_score = 0.0
        
        # Compare with quantum signatures
        for isotope, signature in self.quantum_signatures.items():
            similarity = self._quantum_similarity(state_vector, signature['phase_pattern'])
            if similarity > best_score:
                best_score = similarity
                best_match = isotope
        
        # Require minimum quantum confidence
        if best_score < 0.4:
            return 'Unknown', best_score
        
        return best_match, best_score
    
    def _calculate_state_vector(self, measurement_results):
        """Calculate quantum state vector from measurement results."""
        # Extract key quantum features
        state_features = []
        
        # Probability of all qubits being |0⟩
        prob_all_zero = measurement_results.get('0' * self.num_qubits, 0.0)
        state_features.append(prob_all_zero)
        
        # Probability of all qubits being |1⟩
        prob_all_one = measurement_results.get('1' * self.num_qubits, 0.0)
        state_features.append(prob_all_one)
        
        # Superposition measure
        superposition = 1.0 - (prob_all_zero + prob_all_one)
        state_features.append(superposition)
        
        # Entanglement measure (simplified)
        entanglement = len(measurement_results) / (2 ** self.num_qubits)
        state_features.append(entanglement)
        
        return np.array(state_features)
    
    def _quantum_similarity(self, state_vector, reference_pattern):
        """Calculate quantum similarity between state and reference."""
        # Pad or truncate to match dimensions
        min_len = min(len(state_vector), len(reference_pattern))
        state_truncated = state_vector[:min_len]
        ref_truncated = np.array(reference_pattern[:min_len])
        
        # Calculate quantum fidelity-inspired similarity
        dot_product = np.dot(state_truncated, ref_truncated)
        norm_product = np.linalg.norm(state_truncated) * np.linalg.norm(ref_truncated)
        
        if norm_product > 0:
            similarity = dot_product / norm_product
        else:
            similarity = 0.0
        
        return abs(similarity)
    
    def _quantum_threat_assessment(self, measurement_results, isotope):
        """Assess threat using quantum approach."""
        base_threat = 0.1
        
        if isotope in self.quantum_signatures:
            base_threat = self.quantum_signatures[isotope]['threat_level']
        
        # Quantum enhancement based on measurement entropy
        entropy = self._calculate_quantum_entropy(measurement_results)
        quantum_enhancement = entropy / np.log(2 ** self.num_qubits)  # Normalized entropy
        
        # Combine classical and quantum assessments
        threat_probability = base_threat * (0.7 + 0.3 * quantum_enhancement)
        
        # Add quantum noise
        quantum_noise = np.random.normal(0, 0.03)
        threat_probability = np.clip(threat_probability + quantum_noise, 0.0, 1.0)
        
        return float(threat_probability)
    
    def _calculate_quantum_entropy(self, measurement_results):
        """Calculate quantum entropy from measurement results."""
        entropy = 0.0
        for probability in measurement_results.values():
            if probability > 0:
                entropy -= probability * np.log(probability)
        return entropy
    
    def _quantum_peak_detection(self, energy, counts):
        """Quantum-enhanced peak detection."""
        # Use quantum-inspired algorithm for peak detection
        from scipy.signal import find_peaks
        
        # Apply quantum-inspired smoothing
        quantum_smoothed = self._quantum_smooth(counts)
        
        peaks, properties = find_peaks(
            quantum_smoothed,
            height=np.max(quantum_smoothed) * 0.08,  # Slightly more sensitive
            distance=4,
            prominence=np.max(quantum_smoothed) * 0.04
        )
        
        detected_peaks = []
        for peak_idx in peaks:
            peak_energy = energy[peak_idx]
            peak_intensity = counts[peak_idx]
            peak_significance = peak_intensity / np.max(counts)
            
            detected_peaks.append({
                'energy': float(peak_energy),
                'intensity': float(peak_intensity),
                'significance': float(peak_significance),
                'quantum_enhanced': True
            })
        
        # Sort by significance
        detected_peaks.sort(key=lambda x: x['significance'], reverse=True)
        
        return detected_peaks[:10]
    
    def _quantum_smooth(self, data):
        """Apply quantum-inspired smoothing to data."""
        # Simulate quantum superposition smoothing
        smoothed = np.copy(data).astype(float)
        
        for i in range(1, len(data) - 1):
            # Quantum superposition of neighboring states
            quantum_state = (data[i-1] + 2*data[i] + data[i+1]) / 4
            smoothed[i] = quantum_state
        
        return smoothed
    
    def _quantum_quantity_estimation(self, measurement_results):
        """Estimate material quantity using quantum approach."""
        # Use quantum entropy as a measure of material quantity
        entropy = self._calculate_quantum_entropy(measurement_results)
        max_entropy = np.log(2 ** self.num_qubits)
        
        normalized_entropy = entropy / max_entropy
        
        if normalized_entropy > 0.8:
            return 'Large'
        elif normalized_entropy > 0.5:
            return 'Medium'
        else:
            return 'Small'
    
    def _get_confidence_level(self, confidence):
        """Convert numerical confidence to categorical level."""
        if confidence >= 0.75:
            return 'High'
        elif confidence >= 0.45:
            return 'Medium'
        else:
            return 'Low'
