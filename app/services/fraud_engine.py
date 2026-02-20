import joblib
import os
import numpy as np
from app.explainability.explainer import UPIFraudExplainer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'ensemble_model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'ml', 'scaler.joblib')

class FraudEngine:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.explainer = UPIFraudExplainer()
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)

    def predict_risk(self, amount, time_of_day, velocity, device_age, location_dev, is_new_merchant):
        """
        Predicts fraud risk using ML + hybrid rules.
        """
        # Hybrid Rule: Amount > 100,000 is always HIGH risk
        if amount > 100000:
            return {
                'score': 1.0,
                'label': 'FRAUD',
                'risk_level': 'HIGH',
                'top_features': ['Amount over threshold (Hybrid Rule)'],
                'shap_values': {}
            }

        if self.model is None or self.scaler is None:
            self._load_artifacts()
            if self.model is None:
                return None

        # Features for ML: [amount, time_of_day, velocity, device_age, location_dev, is_new_merchant]
        features = [amount, time_of_day, velocity, device_age, location_dev, is_new_merchant]
        features_arr = np.array(features).reshape(1, -1)
        scaled_features = self.scaler.transform(features_arr)

        # ML Prediction
        prob = float(self.model.predict_proba(scaled_features)[0][1])
        
        # Risk Leveling
        if prob > 0.90:
            label = 'FRAUD'
            risk_level = 'HIGH'
        elif prob > 0.75:
            label = 'SUSPICIOUS'
            risk_level = 'HIGH'
        elif prob > 0.50:
            label = 'SUSPICIOUS'
            risk_level = 'MEDIUM'
        else:
            label = 'LEGIT'
            risk_level = 'LOW'

        # Explanation
        explanation = self.explainer.get_explanation(scaled_features)

        return {
            'score': prob,
            'label': label,
            'risk_level': risk_level,
            'top_features': explanation['top_features'],
            'shap_values': explanation['shap_values']
        }

# Singleton instance
fraud_engine = FraudEngine()
