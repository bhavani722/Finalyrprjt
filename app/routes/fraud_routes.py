from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.models import db, Intent, Transaction, FraudExplanation
from app.services.lifecycle import IntentLifecycle
from app.services.fraud_engine import fraud_engine

fraud_bp = Blueprint('fraud', __name__)

@fraud_bp.route('/fraud/predict', methods=['POST'])
@jwt_required()
def predict_fraud():
    data = request.get_json()
    intent_id = data.get('intent_id')
    features = data.get('features') # [amount, time_of_day, velocity, device_age, location_dev, is_new_merchant]
    
    if not features or len(features) < 6:
        return jsonify(msg="Invalid features"), 400

    # The lifecycle automatically handles PRE_CHECK during intent creation,
    # but this endpoint can be used for manual/explicit checks.
    result = fraud_engine.predict_risk(*features)
    
    if not result:
        return jsonify(msg="Model not available"), 503
        
    return jsonify({
        "intent_id": intent_id,
        "risk_score": result['score'],
        "label": result['label'],
        "risk_level": result['risk_level'],
        "top_features": result['top_features']
    })

@fraud_bp.route('/fraud/explain/<intent_id>', methods=['GET'])
@jwt_required()
def get_explanation(intent_id):
    expl = FraudExplanation.query.filter_by(intent_id=intent_id).first()
    if not expl:
        return jsonify(msg="No explanation found for this intent"), 404
        
    return jsonify({
        "intent_id": intent_id,
        "top_features": expl.top_features,
        "shap_values": expl.shap_values
    })
