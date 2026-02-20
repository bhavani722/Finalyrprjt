from datetime import datetime, timedelta
from app.models.models import db, Intent, Transaction, FraudExplanation, AuditLog
from app.services.fraud_engine import fraud_engine
import uuid

class IntentLifecycle:
    # INTENT_CREATED -> PRE_CHECK -> AWAITING_PAYMENT -> SUCCESS | TIMEOUT | SUSPICIOUS | FRAUD
    
    @staticmethod
    def create_intent(user_id, merchant_id, amount, device_fingerprint, location):
        intent_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        new_intent = Intent(
            intent_id=intent_id,
            user_id=user_id,
            merchant_id=merchant_id,
            amount_expected=amount,
            device_fingerprint=device_fingerprint,
            location=location,
            status='INTENT_CREATED',
            expires_at=expires_at
        )
        db.session.add(new_intent)
        db.session.commit()
        
        # Log creation
        IntentLifecycle._log_audit(intent_id, None, 'INTENT_CREATED')
        
        # Automatically trigger PRE_CHECK
        return IntentLifecycle.run_pre_check(intent_id)

    @staticmethod
    def run_pre_check(intent_id):
        intent = Intent.query.get(intent_id)
        if not intent:
            return None
            
        IntentLifecycle.update_status(intent_id, 'PRE_CHECK')
        
        # In a real app, features like 'velocity' would be calculated from DB
        # For this project, we'll extract features or use defaults if not provided
        # We'll assume standard feature extraction logic here
        time_of_day = datetime.utcnow().hour
        velocity = Transaction.query.filter(
            Transaction.timestamp > datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Simplified feature set for the demo/academic project
        result = fraud_engine.predict_risk(
            amount=intent.amount_expected,
            time_of_day=time_of_day,
            velocity=velocity,
            device_age=30, # Mocked
            location_dev=0.1, # Mocked
            is_new_merchant=0
        )
        
        if result:
            intent.ml_score = result['score']
            intent.ml_label = result['label']
            intent.risk_level = result['risk_level']
            intent.decision_timestamp = datetime.utcnow()
            
            # Record explanation if not legit
            if intent.ml_label != 'LEGIT':
                explanation = FraudExplanation(
                    intent_id=intent_id,
                    shap_values=result['shap_values'],
                    top_features=result['top_features']
                )
                db.session.add(explanation)

            # State transition based on ML
            if intent.ml_score >= 0.90:
                IntentLifecycle.update_status(intent_id, 'FRAUD')
                # Create blocked transaction record
                IntentLifecycle._create_transaction(intent_id, 'FRAUD_BLOCKED')
            elif intent.ml_score >= 0.75:
                IntentLifecycle.update_status(intent_id, 'SUSPICIOUS')
                IntentLifecycle._create_transaction(intent_id, 'PENDING_REVIEW')
            else:
                IntentLifecycle.update_status(intent_id, 'AWAITING_PAYMENT')
                
        db.session.commit()
        return intent

    @staticmethod
    def update_status(intent_id, new_status, changed_by='SYSTEM'):
        intent = Intent.query.get(intent_id)
        if intent and intent.status != new_status:
            old_status = intent.status
            intent.status = new_status
            IntentLifecycle._log_audit(intent_id, old_status, new_status, changed_by)
            db.session.commit()
            return True
        return False

    @staticmethod
    def _log_audit(intent_id, old_status, new_status, changed_by='SYSTEM'):
        log = AuditLog(
            intent_id=intent_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by
        )
        db.session.add(log)

    @staticmethod
    def _create_transaction(intent_id, final_decision):
        intent = Intent.query.get(intent_id)
        txn = Transaction(
            txn_id=str(uuid.uuid4()),
            intent_id=intent_id,
            amount_paid=intent.amount_expected if final_decision != 'FRAUD_BLOCKED' else 0,
            ml_score=intent.ml_score,
            ml_label=intent.ml_label,
            final_decision=final_decision
        )
        db.session.add(txn)

    @staticmethod
    def finalize_transaction(intent_id, success=True):
        intent = Intent.query.get(intent_id)
        if intent:
            new_status = 'SUCCESS' if success else 'FRAUD'
            IntentLifecycle.update_status(intent_id, new_status)
            
            txn = Transaction.query.filter_by(intent_id=intent_id).first()
            if txn:
                txn.final_decision = 'SUCCESS' if success else 'FRAUD_BLOCKED'
            else:
                IntentLifecycle._create_transaction(intent_id, 'SUCCESS' if success else 'FRAUD_BLOCKED')
            
            db.session.commit()
            return True
        return False
