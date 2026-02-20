from app.app import create_app
from app.models.models import db, Intent, Transaction, AuditLog
from app.services.lifecycle import IntentLifecycle
import os

def verify_system():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        try:
            print("--- VERIFICATION START ---")
            
            # Ensure the database is clean for the test if needed, or just proceed
            # No need to create_all as create_app does it
            
            # 1. Test Hybrid Rule (Amount > 100,000)
            print("\n[Testing Hybrid Rule: Amount > 100,000]")
            intent_high = IntentLifecycle.create_intent(
                user_id=1,
                merchant_id=2,
                amount=150000,
                device_fingerprint='test_device',
                location='Mumbai, IN'
            )
            print(f"Intent ID: {intent_high.intent_id}")
            print(f"Status: {intent_high.status}")
            print(f"ML Score: {intent_high.ml_score}")
            print(f"Risk Level: {intent_high.risk_level}")
            
            if intent_high.status != 'FRAUD' or intent_high.risk_level != 'HIGH':
                print("FAIL: Hybrid rule check failed!")
                return
                
            print("✓ Hybrid rule verified.")

            # 2. Test Normal Flow
            print("\n[Testing Normal Flow: Low Amount]")
            intent_low = IntentLifecycle.create_intent(
                user_id=1,
                merchant_id=2,
                amount=500,
                device_fingerprint='test_device',
                location='Mumbai, IN'
            )
            print(f"Intent ID: {intent_low.intent_id}")
            print(f"Status: {intent_low.status}")
            
            # Check Audit logs
            logs = AuditLog.query.filter_by(intent_id=intent_low.intent_id).all()
            print(f"\nAudit Logs for {intent_low.intent_id}:")
            for log in logs:
                print(f"  {log.old_status} -> {log.new_status} (at {log.changed_at})")
            
            if len(logs) < 2:
                print("FAIL: Audit logs missing!")
                return
                
            print("✓ Audit logging verified.")

            # 3. Test Analytics (Summary)
            print("\n[Testing Analytics Summary]")
            total = Transaction.query.count()
            frauds = Transaction.query.filter_by(ml_label='FRAUD').count()
            print(f"Total Transactions: {total}")
            print(f"Total Fraud Detected: {frauds}")
            
            print("\n--- VERIFICATION SUCCESSFUL ---")
            
        except Exception as e:
            print(f"\nEXCEPTION DURING VERIFICATION: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.session.remove() # Clean up session

if __name__ == "__main__":
    verify_system()
