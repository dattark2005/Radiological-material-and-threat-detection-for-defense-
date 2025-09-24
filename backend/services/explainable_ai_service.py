#!/usr/bin/env python3
"""
Explainable AI Service for Radiological Threat Detection
Provides interpretability for both classical and quantum ML models
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance
from sklearn.tree import DecisionTreeClassifier, export_text
import shap
import lime
from lime.lime_tabular import LimeTabularExplainer
import joblib
import io
import base64
from datetime import datetime

class ExplainableAIService:
    """Provide explanations for ML model predictions."""
    
    def __init__(self):
        self.explainers = {}
        self.feature_names = []
        self.models = {}
        
    def load_models_and_data(self, model_paths, feature_names, X_train=None):
        """Load trained models and setup explainers."""
        self.feature_names = feature_names
        
        # Load models
        for name, path in model_paths.items():
            self.models[name] = joblib.load(path)
        
        # Setup LIME explainer if training data is provided
        if X_train is not None:
            self.lime_explainer = LimeTabularExplainer(
                X_train,
                feature_names=feature_names,
                class_names=['Benign', 'Low Threat', 'Medium Threat', 'High Threat'],
                mode='classification'
            )
    
    def explain_prediction(self, model_name, X_instance, method='all'):
        """Generate explanations for a single prediction."""
        model = self.models[model_name]
        explanations = {}
        
        if method in ['all', 'lime']:
            explanations['lime'] = self._lime_explanation(model, X_instance)
        
        if method in ['all', 'shap']:
            explanations['shap'] = self._shap_explanation(model, X_instance)
        
        if method in ['all', 'feature_importance']:
            explanations['feature_importance'] = self._feature_importance_explanation(model)
        
        if method in ['all', 'decision_path']:
            explanations['decision_path'] = self._decision_path_explanation(model, X_instance)
        
        return explanations
    
    def _lime_explanation(self, model, X_instance):
        """Generate LIME explanation."""
        try:
            explanation = self.lime_explainer.explain_instance(
                X_instance.flatten(),
                model.predict_proba,
                num_features=len(self.feature_names)
            )
            
            # Convert to interpretable format
            lime_data = {
                'feature_contributions': explanation.as_list(),
                'prediction_probability': explanation.predict_proba,
                'intercept': explanation.intercept[1] if hasattr(explanation, 'intercept') else 0
            }
            
            # Generate visualization
            fig = explanation.as_pyplot_figure()
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            lime_plot = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)
            
            lime_data['plot'] = lime_plot
            return lime_data
            
        except Exception as e:
            return {'error': f"LIME explanation failed: {str(e)}"}
    
    def _shap_explanation(self, model, X_instance):
        """Generate SHAP explanation."""
        try:
            # Create SHAP explainer based on model type
            if hasattr(model, 'predict_proba'):
                explainer = shap.Explainer(model.predict_proba, self.X_background)
            else:
                explainer = shap.Explainer(model, self.X_background)
            
            shap_values = explainer(X_instance.reshape(1, -1))
            
            # Generate waterfall plot
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.waterfall_plot(shap_values[0], show=False)
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            shap_plot = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)
            
            return {
                'shap_values': shap_values.values.tolist(),
                'base_value': shap_values.base_values.tolist(),
                'feature_names': self.feature_names,
                'plot': shap_plot
            }
            
        except Exception as e:
            return {'error': f"SHAP explanation failed: {str(e)}"}
    
    def _feature_importance_explanation(self, model):
        """Generate feature importance explanation."""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_[0])
            else:
                return {'error': 'Model does not support feature importance'}
            
            # Create feature importance plot
            fig, ax = plt.subplots(figsize=(10, 6))
            indices = np.argsort(importances)[::-1]
            
            plt.bar(range(len(importances)), importances[indices])
            plt.xticks(range(len(importances)), 
                      [self.feature_names[i] for i in indices], 
                      rotation=45, ha='right')
            plt.title('Feature Importance')
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            importance_plot = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)
            
            return {
                'importances': importances.tolist(),
                'feature_names': self.feature_names,
                'plot': importance_plot
            }
            
        except Exception as e:
            return {'error': f"Feature importance failed: {str(e)}"}
    
    def _decision_path_explanation(self, model, X_instance):
        """Generate decision path explanation for tree-based models."""
        try:
            if not hasattr(model, 'decision_path'):
                return {'error': 'Model does not support decision path'}
            
            # Get decision path
            leaf_id = model.apply(X_instance.reshape(1, -1))
            feature = model.tree_.feature
            threshold = model.tree_.threshold
            
            # Build decision path text
            decision_path = []
            node_indicator = model.decision_path(X_instance.reshape(1, -1))
            leaf_id = model.apply(X_instance.reshape(1, -1))
            
            sample_id = 0
            node_index = node_indicator.toarray()[sample_id].nonzero()[0]
            
            for node_id in node_index:
                if leaf_id[sample_id] == node_id:
                    continue
                
                if X_instance[feature[node_id]] <= threshold[node_id]:
                    threshold_sign = "<="
                else:
                    threshold_sign = ">"
                
                decision_path.append(
                    f"{self.feature_names[feature[node_id]]} {threshold_sign} {threshold[node_id]:.3f}"
                )
            
            return {
                'decision_path': decision_path,
                'leaf_id': int(leaf_id[0])
            }
            
        except Exception as e:
            return {'error': f"Decision path failed: {str(e)}"}
    
    def generate_global_explanations(self, model_name, X_test, y_test):
        """Generate global model explanations."""
        model = self.models[model_name]
        explanations = {}
        
        # Permutation importance
        try:
            perm_importance = permutation_importance(
                model, X_test, y_test, n_repeats=10, random_state=42
            )
            
            explanations['permutation_importance'] = {
                'importances_mean': perm_importance.importances_mean.tolist(),
                'importances_std': perm_importance.importances_std.tolist(),
                'feature_names': self.feature_names
            }
        except Exception as e:
            explanations['permutation_importance'] = {'error': str(e)}
        
        # Model performance by feature groups
        explanations['feature_group_analysis'] = self._analyze_feature_groups(model, X_test, y_test)
        
        return explanations
    
    def _analyze_feature_groups(self, model, X_test, y_test):
        """Analyze model performance by feature groups."""
        feature_groups = {
            'statistical': ['total_counts', 'max_count', 'mean_energy', 'std_energy'],
            'spectral_shape': ['skewness', 'kurtosis'],
            'energy_regions': ['low_energy_counts', 'mid_energy_counts', 'high_energy_counts'],
            'peaks': [f'peak{i}_energy' for i in range(1, 6)] + [f'peak{i}_intensity' for i in range(1, 6)]
        }
        
        group_analysis = {}
        
        for group_name, features in feature_groups.items():
            # Find indices of features in this group
            feature_indices = []
            for feature in features:
                if feature in self.feature_names:
                    feature_indices.append(self.feature_names.index(feature))
            
            if feature_indices:
                # Test model performance with only this feature group
                X_group = X_test[:, feature_indices]
                try:
                    accuracy = model.score(X_group, y_test)
                    group_analysis[group_name] = {
                        'accuracy': accuracy,
                        'features': features,
                        'num_features': len(feature_indices)
                    }
                except:
                    group_analysis[group_name] = {'error': 'Could not evaluate this group'}
        
        return group_analysis
    
    def explain_quantum_model(self, quantum_model, X_instance):
        """Provide explanations for quantum model predictions."""
        explanations = {
            'quantum_specific': {
                'circuit_depth': 'Information about quantum circuit depth',
                'entanglement_measure': 'Measure of quantum entanglement used',
                'quantum_advantage': 'Analysis of quantum vs classical advantage',
                'feature_encoding': 'How classical features are encoded in quantum states'
            }
        }
        
        # Quantum-specific explanations would go here
        # This is a placeholder for quantum interpretability methods
        
        return explanations
    
    def generate_explanation_report(self, model_name, X_instance, prediction, confidence):
        """Generate comprehensive explanation report."""
        explanations = self.explain_prediction(model_name, X_instance)
        
        report = {
            'prediction': {
                'class': prediction,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            },
            'explanations': explanations,
            'summary': self._generate_explanation_summary(explanations, prediction)
        }
        
        return report
    
    def _generate_explanation_summary(self, explanations, prediction):
        """Generate human-readable explanation summary."""
        summary = []
        
        # LIME summary
        if 'lime' in explanations and 'feature_contributions' in explanations['lime']:
            top_features = sorted(
                explanations['lime']['feature_contributions'], 
                key=lambda x: abs(x[1]), 
                reverse=True
            )[:3]
            
            summary.append("Top contributing factors:")
            for feature, contribution in top_features:
                direction = "increases" if contribution > 0 else "decreases"
                summary.append(f"- {feature} {direction} threat probability by {abs(contribution):.3f}")
        
        # Feature importance summary
        if 'feature_importance' in explanations:
            summary.append("\nMost important features for this model:")
            # Add feature importance summary
        
        return "\n".join(summary)
    
    def create_explanation_dashboard(self, explanations):
        """Create interactive explanation dashboard."""
        # This would create an interactive dashboard
        # For now, return structured data for frontend rendering
        
        dashboard_data = {
            'charts': [],
            'tables': [],
            'insights': []
        }
        
        # Add charts for each explanation type
        for explanation_type, data in explanations.items():
            if 'plot' in data:
                dashboard_data['charts'].append({
                    'type': explanation_type,
                    'plot': data['plot'],
                    'title': f"{explanation_type.upper()} Explanation"
                })
        
        return dashboard_data

# Integration with existing ML service
def integrate_explainable_ai():
    """Integration function for existing ML service."""
    
    # Add to existing MLService class
    explainable_ai_methods = """
    def explain_prediction(self, spectrum_data, model_type='classical'):
        '''Add explanation to existing analyze method.'''
        
        # Get prediction first
        prediction = self.analyze(spectrum_data)
        
        # Generate explanations
        explainer = ExplainableAIService()
        explainer.load_models_and_data(
            model_paths={'model': self.model_path},
            feature_names=self.feature_names
        )
        
        explanations = explainer.explain_prediction(
            'model', 
            self.extract_features(spectrum_data)
        )
        
        # Add explanations to prediction result
        prediction['explanations'] = explanations
        prediction['explanation_summary'] = explainer._generate_explanation_summary(
            explanations, 
            prediction['classified_isotope']
        )
        
        return prediction
    """
    
    return explainable_ai_methods

if __name__ == "__main__":
    print("Explainable AI service ready for integration!")
