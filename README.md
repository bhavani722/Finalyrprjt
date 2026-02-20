# UPI Fraud Detection System

A real-time proactive UPI fraud detection system built with Flask, SQLAlchemy, Scikit-Learn (Ensemble Model), and SHAP for explainability.

## Features
- **Intent-Based Monitoring**: Detects fraud at the QR scan stage before PIN entry.
- **ML Risk Scoring**: Uses an ensemble of Logistic Regression and Random Forest.
- **Borderline-SMOTE**: Handles imbalanced transaction data.
- **SHAP Explanations**: Provides human-readable reasons for fraud flags.
- **Role-Based Access Control**: Separate interfaces for Users, Merchants, and Admins.
- **Aesthetic UI**: Modern, dark-themed vanilla JS frontend.

## Project Structure
```
upi-fraud-detection/
├── app/
│   ├── app.py                     # Flask entry point
│   ├── models/                    # DB Models
│   ├── routes/                    # API Endpoints
│   ├── services/                  # Intent Lifecycle Logic
│   ├── ml/                        # Model Training
│   ├── explainability/            # SHAP Explainer
│   └── auth/                      # JWT & RBAC
├── frontend/                      # Vanilla JS UI
├── data/                          # DB and CSV storage
└── requirements.txt
```

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the ML Model**:
   ```bash
   python app/ml/trainer.py
   ```

3. **Run the Server**:
   ```bash
   python app/app.py
   ```

4. **Access the UI**:
   - User Dashboard: `frontend/index.html`
   - Merchant Dashboard: `frontend/merchant.html`
   - Admin Panel: `frontend/admin.html`

## Test Credentials
- **User**: `user1` / `password123`
- **Merchant**: `merchant1` / `password123`
- **Admin**: `admin1` / `admin123`
