from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False) # USER, MERCHANT, ADMIN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Intent(db.Model):
    __tablename__ = 'intents'
    intent_id = db.Column(db.String(36), primary_key=True, index=True) # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount_expected = db.Column(db.Float, nullable=False)
    device_fingerprint = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='INTENT_CREATED', index=True)
    ml_score = db.Column(db.Float)
    ml_label = db.Column(db.String(20))
    risk_level = db.Column(db.String(20)) # LOW, MEDIUM, HIGH
    decision_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id])
    merchant = db.relationship('User', foreign_keys=[merchant_id])

class Transaction(db.Model):
    __tablename__ = 'transactions'
    txn_id = db.Column(db.String(36), primary_key=True)
    intent_id = db.Column(db.String(36), db.ForeignKey('intents.intent_id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    ml_score = db.Column(db.Float)
    ml_label = db.Column(db.String(20)) # FRAUD, LEGIT
    final_decision = db.Column(db.String(20)) # SUCCESS, FRAUD_BLOCKED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    intent = db.relationship('Intent', backref=db.backref('transaction', uselist=False))

class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    os_version = db.Column(db.String(50))
    sim_hash = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

class FraudExplanation(db.Model):
    __tablename__ = 'fraud_explanations'
    id = db.Column(db.Integer, primary_key=True)
    intent_id = db.Column(db.String(36), db.ForeignKey('intents.intent_id'), nullable=False)
    shap_values = db.Column(db.JSON)
    top_features = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    intent_id = db.Column(db.String(36), db.ForeignKey('intents.intent_id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.String(80), default='SYSTEM')
