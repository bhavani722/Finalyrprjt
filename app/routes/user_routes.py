from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import User, Intent, db
from app.services.lifecycle import IntentLifecycle
from app.auth.jwt_utils import role_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/intent/create', methods=['POST'])
@jwt_required()
@role_required(['USER'])
def create_intent():
    data = request.get_json()
    user_id = get_jwt_identity()
    merchant_id = data.get('merchant_id')
    amount = data.get('amount')
    device_fingerprint = data.get('device_fingerprint')
    location = data.get('location')
    
    if not all([merchant_id, amount, device_fingerprint, location]):
        return jsonify(msg="Missing required fields"), 400
        
    intent = IntentLifecycle.create_intent(user_id, merchant_id, amount, device_fingerprint, location)
    
    return jsonify({
        "msg": "Intent created",
        "intent_id": intent.intent_id,
        "status": intent.status,
        "expires_at": intent.expires_at.isoformat()
    }), 201

@user_bp.route('/intent/status/<intent_id>', methods=['GET'])
@jwt_required()
def get_intent_status(intent_id):
    intent = Intent.query.get(intent_id)
    if not intent:
        return jsonify(msg="Intent not found"), 404
        
    # Security: Only user or merchant or admin can view
    current_user_id = int(get_jwt_identity())
    if intent.user_id != current_user_id and intent.merchant_id != current_user_id:
        # Check if admin
        from flask_jwt_extended import get_jwt
        if get_jwt().get('role') != 'ADMIN':
            return jsonify(msg="Unauthorized"), 403
            
    return jsonify({
        "intent_id": intent.intent_id,
        "status": intent.status,
        "amount": intent.amount_expected,
        "merchant_id": intent.merchant_id
    })

@user_bp.route('/scan-qr', methods=['POST'])
@jwt_required()
@role_required(['USER', 'ADMIN'])
def scan_qr():
    data = request.get_json()
    payload = data.get('payload')
    if not payload or '|' not in payload:
        return jsonify(msg="Invalid QR payload"), 400
        
    merchant_id, amount = payload.split("|")
    user_id = get_jwt_identity()

    intent = IntentLifecycle.create_intent(
        user_id=user_id,
        merchant_id=int(merchant_id),
        amount=float(amount),
        device_fingerprint="mobile_device_sim",
        location="User Geo-Location"
    )

    return jsonify({
        "intent_id": intent.intent_id,
        "status": intent.status,
        "ml_score": intent.ml_score,
        "risk_level": intent.risk_level,
        "amount": intent.amount_expected
    })
