"""
Lock Contention Risk Predictor

Loads trained model and makes predictions on new contention metrics.
Used by the CLI dashboard for live risk assessment.
"""

import pickle
import numpy as np
from typing import Dict, Tuple

class ContentionPredictor:
    """Wrapper for loaded ML model with prediction interface."""
    
    def __init__(self, 
                 model_path='model.pkl',
                 scaler_path='scaler.pkl', 
                 metadata_path='model_metadata.pkl'):
        """Load model, scaler, and metadata."""
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        self.label_encoder = self.metadata['label_encoder']
        self.feature_names = self.metadata['feature_names']
        self.classes = self.metadata['classes']
    
    def predict(self, metrics: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """
        Predict contention risk from metrics.
        
        Args:
            metrics: Dictionary with keys matching feature_names
        
        Returns:
            (predicted_risk, probability_distribution)
        """
        
        # Extract features in correct order
        features = np.array([[
            metrics['avg_wait_time_ms'],
            metrics['max_wait_time_ms'],
            metrics['contention_frequency'],
            metrics['blocked_thread_percentage'],
            metrics['wait_time_growth_rate']
        ]])
        
        # Standardize
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Decode label
        risk_level = self.label_encoder.inverse_transform([prediction])[0]
        
        # Create probability dict
        prob_dict = {
            cls: float(prob) 
            for cls, prob in zip(self.classes, probabilities)
        }
        
        return risk_level, prob_dict

if __name__ == '__main__':
    # Test prediction
    predictor = ContentionPredictor()
    
    test_metrics = {
        'avg_wait_time_ms': 75.0,
        'max_wait_time_ms': 250.0,
        'contention_frequency': 25,
        'blocked_thread_percentage': 20.0,
        'wait_time_growth_rate': 1.5
    }
    
    risk, probs = predictor.predict(test_metrics)
    
    print("Test prediction:")
    print(f"Metrics: {test_metrics}")
    print(f"Predicted risk: {risk}")
    print(f"Probabilities: {probs}")
