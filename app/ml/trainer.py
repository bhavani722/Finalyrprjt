import numpy as np
import pandas as pd
import joblib
import os
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
from imblearn.over_sampling import BorderlineSMOTE

# Set paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'ensemble_model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'ml', 'scaler.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'ml', 'model_metrics.json')
CSV_PATH = os.path.join(DATA_DIR, 'upi_transactions.csv')

def train_model():
    print("Loading data...")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Required transaction data missing at {CSV_PATH}. Automated generation disabled.")
    
    df = pd.read_csv(CSV_PATH)
    
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Preprocessing
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Handle Imbalance with BorderlineSMOTE
    print("Applying Borderline-SMOTE...")
    smote = BorderlineSMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    
    # Models
    lr = LogisticRegression(random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # Ensemble
    print("Training Ensemble Model...")
    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf)],
        voting='soft'
    )
    
    ensemble.fit(X_train_res, y_train_res)
    
    # Evaluation
    y_pred = ensemble.predict(X_test_scaled)
    y_prob = ensemble.predict_proba(X_test_scaled)[:, 1]
    
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred)),
        'recall': float(recall_score(y_test, y_pred)),
        'f1': float(f1_score(y_test, y_pred)),
        'roc_auc': float(roc_auc_score(y_test, y_prob)),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print("\nModel Evaluation:")
    for k, v in metrics.items():
        if k != 'confusion_matrix':
            print(f"{k.capitalize()}: {v}")
    
    # Save artifacts
    joblib.dump(ensemble, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Model saved to {MODEL_PATH}")
    print(f"Metrics saved to {METRICS_PATH}")
    
    return metrics

if __name__ == "__main__":
    from datetime import datetime
    try:
        train_model()
    except Exception as e:
        print(f"Training failed: {e}")

if __name__ == "__main__":
    train_model()
