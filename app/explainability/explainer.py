import shap
import joblib
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'ensemble_model.joblib')

class UPIFraudExplainer:
    def __init__(self):
        self.model = None
        self.explainer = None
        self.feature_names = ['amount', 'time_of_day', 'velocity', 'device_age', 'location_dev', 'is_new_merchant']
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.dump(None, 'temp.joblib') # Placeholder for logic, will load actual model
            self.model = joblib.load(MODEL_PATH)
            # Use KernelExplainer for ensemble or TreeExplainer if we only used RF
            # Since we have an ensemble, KernelExplainer is more general but slower.
            # However, for RF part we can use TreeExplainer. 
            # Let's use the RF model from the ensemble for faster explanations if possible,
            # or just KernelExplainer on a small background dataset.
            
    def get_explanation(self, input_data):
        """
        input_data: Scaled numpy array or list of features
        Returns: Dict with SHAP values and human-readable top features
        """
        if self.model is None:
            self._load_model()
            
        # We'll use the RF estimator from the voting classifier for SHAP if available
        rf_model = self.model.named_estimators_['rf']
        
        # TreeExplainer is much faster
        explainer = shap.TreeExplainer(rf_model)
        shap_values = explainer.shap_values(input_data)
        
        # shap_values is a list for multi-class [class0, class1]
        # For binary classification (fraud is class 1), use index 1
        curr_shap = shap_values[1] if isinstance(shap_values, list) else shap_values
        
        # Map values to feature names
        impact_dict = dict(zip(self.feature_names, curr_shap[0]))
        
        # Sort by absolute impact
        sorted_impact = sorted(impact_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Top features names
        top_features = [f"{k} ({'Increases' if v > 0 else 'Decreases'} risk)" for k, v in sorted_impact[:3]]
        
        return {
            'shap_values': impact_dict,
            'top_features': top_features,
            'summary': f"Risk influenced primarily by: {', '.join([k for k, v in sorted_impact[:2]])}"
        }

if __name__ == "__main__":
    # Test stub
    # explainer = UPIFraudExplainer()
    pass
