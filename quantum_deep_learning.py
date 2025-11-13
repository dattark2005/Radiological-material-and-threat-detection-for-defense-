#!/usr/bin/env python3
"""
Quantum Deep Learning for Radiological Threat Detection
Advanced Quantum Neural Networks with multiple layers and quantum attention mechanisms
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime
import os

# Qiskit imports for advanced quantum circuits
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter, ParameterVector
from qiskit_aer import AerSimulator
from qiskit.primitives import Sampler
from qiskit_machine_learning.neural_networks import SamplerQNN
from qiskit.circuit.library import RealAmplitudes, EfficientSU2, TwoLocal
from qiskit_algorithms.optimizers import ADAM, COBYLA, SPSA

class QuantumLayer:
    """Individual quantum layer for deep quantum networks."""
    
    def __init__(self, num_qubits, num_layers=2, entanglement='circular'):
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.entanglement = entanglement
        self.circuit = None
        self.parameters = None
        self.create_layer()
    
    def create_layer(self):
        """Create a parameterized quantum layer."""
        self.circuit = TwoLocal(
            num_qubits=self.num_qubits,
            rotation_blocks=['ry', 'rz'],
            entanglement_blocks='cz',
            entanglement=self.entanglement,
            reps=self.num_layers
        )
        self.parameters = self.circuit.parameters
    
    def get_circuit(self):
        """Return the quantum circuit."""
        return self.circuit

class QuantumAttentionMechanism:
    """Quantum attention mechanism for focusing on important spectral features."""
    
    def __init__(self, num_qubits):
        self.num_qubits = num_qubits
        self.attention_circuit = None
        self.create_attention_circuit()
    
    def create_attention_circuit(self):
        """Create quantum attention circuit."""
        self.attention_circuit = QuantumCircuit(self.num_qubits)
        
        # Create attention parameters
        attention_params = ParameterVector('attention', self.num_qubits)
        
        # Apply attention rotations
        for i in range(self.num_qubits):
            self.attention_circuit.ry(attention_params[i], i)
        
        # Add entanglement for attention correlation
        for i in range(self.num_qubits - 1):
            self.attention_circuit.cx(i, i + 1)
    
    def get_circuit(self):
        """Return the attention circuit."""
        return self.attention_circuit

class QuantumDeepNetwork:
    """Deep Quantum Neural Network for radiological classification."""
    
    def __init__(self, num_features=8, num_qubits=6, num_layers=3):
        self.num_features = num_features
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        
        # Network components
        self.encoding_circuit = None
        self.quantum_layers = []
        self.attention_mechanism = None
        self.measurement_circuit = None
        self.qnn = None
        
        # Training components
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.trained = False
        
        self.create_network()
    
    def create_encoding_circuit(self):
        """Create data encoding circuit."""
        encoding_circuit = QuantumCircuit(self.num_qubits)
        
        # Feature parameters
        feature_params = ParameterVector('x', self.num_features)
        
        # Amplitude encoding with rotation gates
        for i in range(min(self.num_features, self.num_qubits)):
            encoding_circuit.ry(feature_params[i], i)
        
        # Add entanglement for feature correlation
        for i in range(self.num_qubits - 1):
            encoding_circuit.cx(i, i + 1)
        
        return encoding_circuit, feature_params
    
    def create_network(self):
        """Create the complete quantum deep network."""
        print("🏗️ Building Quantum Deep Network...")
        
        # 1. Data encoding layer
        self.encoding_circuit, self.feature_params = self.create_encoding_circuit()
        
        # 2. Multiple quantum layers (deep structure)
        for layer_idx in range(self.num_layers):
            layer = QuantumLayer(
                num_qubits=self.num_qubits,
                num_layers=2,
                entanglement='circular' if layer_idx % 2 == 0 else 'linear'
            )
            self.quantum_layers.append(layer)
        
        # 3. Quantum attention mechanism
        self.attention_mechanism = QuantumAttentionMechanism(self.num_qubits)
        
        # 4. Combine all circuits
        full_circuit = QuantumCircuit(self.num_qubits)
        
        # Add encoding
        full_circuit.compose(self.encoding_circuit, inplace=True)
        
        # Add quantum layers
        for layer in self.quantum_layers:
            full_circuit.compose(layer.get_circuit(), inplace=True)
        
        # Add attention mechanism
        full_circuit.compose(self.attention_mechanism.get_circuit(), inplace=True)
        
        # 5. Create Quantum Neural Network
        self.qnn = SamplerQNN(
            circuit=full_circuit,
            input_params=self.feature_params,
            weight_params=[p for layer in self.quantum_layers for p in layer.parameters] + 
                         list(self.attention_mechanism.attention_circuit.parameters),
            sampler=Sampler()
        )
        
        print(f"✅ Network created:")
        print(f"   - Qubits: {self.num_qubits}")
        print(f"   - Quantum layers: {self.num_layers}")
        print(f"   - Total parameters: {self.qnn.num_weights}")
        print(f"   - Circuit depth: {full_circuit.depth()}")

class HybridQuantumClassifier(nn.Module):
    """Hybrid classical-quantum neural network."""
    
    def __init__(self, quantum_network, num_classes):
        super().__init__()
        self.quantum_network = quantum_network
        self.num_classes = num_classes
        
        # Classical post-processing layers
        self.classical_layers = nn.Sequential(
            nn.Linear(2**quantum_network.num_qubits, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes),
            nn.Softmax(dim=1)
        )
    
    def forward(self, x):
        # Process through quantum network
        quantum_output = []
        for sample in x:
            qnn_result = self.quantum_network.qnn.forward(sample.numpy(), np.random.random(self.quantum_network.qnn.num_weights))
            quantum_output.append(qnn_result)
        
        quantum_tensor = torch.tensor(quantum_output, dtype=torch.float32)
        
        # Process through classical layers
        output = self.classical_layers(quantum_tensor)
        return output

class QuantumDeepLearningTrainer:
    """Trainer for quantum deep learning models."""
    
    def __init__(self, num_features=8, num_qubits=6, num_layers=3):
        self.quantum_network = QuantumDeepNetwork(num_features, num_qubits, num_layers)
        self.hybrid_model = None
        self.optimizer = None
        self.criterion = nn.CrossEntropyLoss()
        
    def prepare_data(self, csv_file):
        """Load and prepare data for quantum deep learning."""
        print("📊 Preparing data for Quantum Deep Learning...")
        
        # Load CSV data
        df = pd.read_csv(csv_file)
        
        # Group by file to create spectrum features
        spectra_data = []
        
        for file_name in df['File'].unique():
            file_data = df[df['File'] == file_name].sort_values('Channel')
            
            if len(file_data) > 0:
                counts = file_data['Counts'].values
                energies = file_data['Energy_keV'].values
                
                # Advanced feature extraction for deep learning
                features = self.extract_deep_features(counts, energies)
                
                spectra_data.append({
                    'file': file_name,
                    'isotope': file_data['Isotope'].iloc[0],
                    'features': features
                })
        
        X = np.array([item['features'] for item in spectra_data])
        y = np.array([item['isotope'] for item in spectra_data])
        
        print(f"   - Created {len(X)} spectrum samples")
        print(f"   - Feature dimension: {X.shape[1]}")
        print(f"   - Unique isotopes: {np.unique(y)}")
        
        return X, y
    
    def extract_deep_features(self, counts, energies):
        """Extract advanced features for deep quantum learning."""
        if len(counts) == 0:
            return np.zeros(self.quantum_network.num_features)
        
        # Normalize
        total_counts = np.sum(counts)
        if total_counts > 0:
            normalized_counts = counts / total_counts
        else:
            normalized_counts = counts
        
        features = []
        
        # 1. Statistical moments
        features.extend([
            np.mean(normalized_counts),
            np.std(normalized_counts),
            np.var(normalized_counts),
        ])
        
        # 2. Energy-weighted features
        if len(energies) == len(counts):
            weighted_energy = np.sum(normalized_counts * energies) / np.sum(normalized_counts) if np.sum(normalized_counts) > 0 else 0
            features.append(weighted_energy)
        else:
            features.append(0)
        
        # 3. Peak characteristics
        peaks = self.find_peaks(counts)
        features.extend([
            len(peaks),
            np.max(counts) if len(counts) > 0 else 0,
        ])
        
        # 4. Spectral entropy
        entropy = -np.sum(normalized_counts * np.log(normalized_counts + 1e-10))
        features.append(entropy)
        
        # 5. High-frequency components
        if len(counts) > 1:
            diff = np.diff(counts)
            features.append(np.std(diff))
        else:
            features.append(0)
        
        # Pad or truncate to required size
        features = np.array(features)
        if len(features) < self.quantum_network.num_features:
            features = np.pad(features, (0, self.quantum_network.num_features - len(features)))
        else:
            features = features[:self.quantum_network.num_features]
        
        return features
    
    def find_peaks(self, counts, threshold=0.1):
        """Simple peak finding."""
        if len(counts) == 0:
            return []
        
        max_count = np.max(counts)
        min_height = max_count * threshold
        
        peaks = []
        for i in range(1, len(counts)-1):
            if (counts[i] > counts[i-1] and 
                counts[i] > counts[i+1] and 
                counts[i] > min_height):
                peaks.append(i)
        
        return peaks
    
    def train(self, X, y, epochs=50, batch_size=16, learning_rate=0.001):
        """Train the quantum deep learning model."""
        print("🚀 Training Quantum Deep Learning Model...")
        
        # Prepare data
        X_scaled = self.quantum_network.scaler.fit_transform(X)
        y_encoded = self.quantum_network.label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Convert to tensors
        X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
        X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.long)
        y_test_tensor = torch.tensor(y_test, dtype=torch.long)
        
        # Create hybrid model
        num_classes = len(np.unique(y_encoded))
        self.hybrid_model = HybridQuantumClassifier(self.quantum_network, num_classes)
        self.optimizer = optim.Adam(self.hybrid_model.parameters(), lr=learning_rate)
        
        print(f"   - Training samples: {len(X_train)}")
        print(f"   - Test samples: {len(X_test)}")
        print(f"   - Classes: {num_classes}")
        print(f"   - Epochs: {epochs}")
        
        # Training loop
        train_losses = []
        train_accuracies = []
        
        for epoch in range(epochs):
            self.hybrid_model.train()
            epoch_loss = 0
            correct_predictions = 0
            
            # Mini-batch training
            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i+batch_size]
                batch_y = y_train_tensor[i:i+batch_size]
                
                self.optimizer.zero_grad()
                
                # Forward pass
                outputs = self.hybrid_model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
                
                # Calculate accuracy
                _, predicted = torch.max(outputs.data, 1)
                correct_predictions += (predicted == batch_y).sum().item()
            
            # Calculate metrics
            avg_loss = epoch_loss / (len(X_train_tensor) // batch_size)
            accuracy = correct_predictions / len(X_train_tensor)
            
            train_losses.append(avg_loss)
            train_accuracies.append(accuracy)
            
            if (epoch + 1) % 10 == 0:
                print(f"   Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.4f}, Accuracy = {accuracy:.4f}")
        
        # Final evaluation
        self.hybrid_model.eval()
        with torch.no_grad():
            test_outputs = self.hybrid_model(X_test_tensor)
            _, test_predicted = torch.max(test_outputs.data, 1)
            test_accuracy = (test_predicted == y_test_tensor).sum().item() / len(y_test_tensor)
        
        print(f"✅ Training completed!")
        print(f"   - Final training accuracy: {train_accuracies[-1]:.4f}")
        print(f"   - Test accuracy: {test_accuracy:.4f}")
        
        # Plot training curves
        self.plot_training_curves(train_losses, train_accuracies)
        
        self.quantum_network.trained = True
        
        return {
            'train_accuracy': train_accuracies[-1],
            'test_accuracy': test_accuracy,
            'train_losses': train_losses,
            'train_accuracies': train_accuracies
        }
    
    def plot_training_curves(self, losses, accuracies):
        """Plot training curves."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss curve
        ax1.plot(losses)
        ax1.set_title('Training Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.grid(True)
        
        # Accuracy curve
        ax2.plot(accuracies)
        ax2.set_title('Training Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('quantum_deep_learning_curves.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("📈 Training curves saved as 'quantum_deep_learning_curves.png'")

def main():
    """Main training pipeline for Quantum Deep Learning."""
    print("🌟 Quantum Deep Learning for Radiological Threat Detection")
    print("=" * 70)
    
    # Initialize trainer
    trainer = QuantumDeepLearningTrainer(
        num_features=8,
        num_qubits=6,
        num_layers=3
    )
    
    # Load data
    csv_file = "converted_csv/all_spectra_master.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("Please run data_convert.py first to convert SPE files to CSV")
        return
    
    try:
        X, y = trainer.prepare_data(csv_file)
        
        # Train model
        results = trainer.train(X, y, epochs=30, batch_size=8, learning_rate=0.001)
        
        print("\n🎯 Training Summary:")
        print(f"   - Dataset: {len(X)} spectra")
        print(f"   - Features: {X.shape[1]}")
        print(f"   - Classes: {len(np.unique(y))}")
        print(f"   - Final Test Accuracy: {results['test_accuracy']:.4f}")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
