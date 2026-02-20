import os
import uuid
import qrcode
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Intent, User
from app.services.lifecycle import IntentLifecycle
from app.auth.jwt_utils import role_required

merchant_bp = Blueprint('merchant', __name__)

@merchant_bp.route('/merchant/pending', methods=['GET'])
@jwt_required()
@role_required(['MERCHANT'])
def get_pending_intents():
    merchant_id = get_jwt_identity()
    pending = Intent.query.filter_by(merchant_id=merchant_id, status='AWAITING_PAYMENT').all()
    
    return jsonify([{
        "intent_id": i.intent_id,
        "amount": i.amount_expected,
        "user_id": i.user_id,
        "created_at": i.created_at.isoformat()
    } for i in pending])

@merchant_bp.route('/merchant/create-intent', methods=['POST'])
@jwt_required()
@role_required(['MERCHANT', 'ADMIN'])
def merchant_create_intent():
    # Helper for the SPA to simulate intent creation
    data = request.get_json()
    user = User.query.filter_by(role='USER').first() # Default user for demo
    user_id = user.id if user else 1
    
    merchant_id = get_jwt_identity()
    amount = data.get('amount')
    device = data.get('device_fingerprint', 'df_9a12c8b4')
    location = data.get('location', 'Bangalore, IN')
    
    intent = IntentLifecycle.create_intent(user_id, merchant_id, amount, device, location)
    
    return jsonify({
        "intent_id": intent.intent_id,
        "status": intent.status,
        "ml_score": intent.ml_score,
        "risk_level": intent.risk_level,
        "expires_at": intent.expires_at.isoformat()
    })

@merchant_bp.route('/merchant/process-payment', methods=['POST'])
@jwt_required()
def process_payment():
    data = request.get_json()
    intent_id = data.get('intent_id')
    success = data.get('success', True)
    
    IntentLifecycle.finalize_transaction(intent_id, success=success)
    
    return jsonify({
        "msg": "Transaction processed",
        "status": "SUCCESS" if success else "FRAUD"
    })

@merchant_bp.route('/merchant/generate-qr', methods=['POST'])
@jwt_required()
@role_required(['MERCHANT', 'ADMIN'])
def generate_qr():
    data = request.get_json()
    merchant_id = get_jwt_identity()
    amount = data.get('amount')

    # Ensure static/qrs directory exists
    qr_dir = os.path.join(current_app.static_folder, 'qrs')
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)

    payload = f"{merchant_id}|{amount}"
    qr = qrcode.make(payload)

    qr_filename = f"{uuid.uuid4()}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    qr.save(qr_path)

    return jsonify({"qr_path": f"/qrs/{qr_filename}"})

@merchant_bp.route('/merchant/alerts', methods=['GET'])
@jwt_required()
@role_required(['MERCHANT', 'ADMIN'])
def merchant_alerts():
    # Only show SUSPICIOUS alerts for this merchant
    merchant_id = get_jwt_identity()
    suspicious = Intent.query.filter_by(
        merchant_id=merchant_id,
        status='SUSPICIOUS'
    ).order_by(Intent.created_at.desc()).first()

    if suspicious:
        return jsonify({
            "new_alert": True,
            "amount": suspicious.amount_expected,
            "risk_level": suspicious.risk_level,
            "ml_score": suspicious.ml_score
        })
    return jsonify({"new_alert": False})
