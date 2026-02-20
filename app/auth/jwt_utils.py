from flask_jwt_extended import create_access_token, get_jwt, verify_jwt_in_request
from functools import wraps
from flask import jsonify

def create_token(user_id, role):
    additional_claims = {"role": role}
    return create_access_token(identity=str(user_id), additional_claims=additional_claims)

def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") in roles:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Insufficient permissions"), 403
        return decorator
    return wrapper
