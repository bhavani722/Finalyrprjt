import time
import threading
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os
from datetime import datetime, timedelta
from sqlalchemy import inspect

# Import models
from app.models.models import db, User, Intent
from app.services.lifecycle import IntentLifecycle

# Import routes
from app.routes.user_routes import user_bp
from app.routes.merchant_routes import merchant_bp
from app.routes.admin_routes import admin_bp
from app.routes.fraud_routes import fraud_bp

def start_timeout_scheduler(app):
    def check_timeouts():
        with app.app_context():
            while True:
                try:
                    now = datetime.utcnow()
                    expired_intents = Intent.query.filter(
                        Intent.status == 'AWAITING_PAYMENT',
                        Intent.expires_at < now
                    ).all()
                    
                    for intent in expired_intents:
                        IntentLifecycle.update_status(intent.intent_id, 'TIMEOUT')
                        print(f"Intent {intent.intent_id} timed out.")
                        
                except Exception as e:
                    print(f"Scheduler safe skip: {e}")
                
                time.sleep(30)
    
    thread = threading.Thread(target=check_timeouts, daemon=True)
    thread.start()

def run_schema_migration(app):
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('intents')]

        with db.engine.connect() as conn:
            if 'ml_score' not in columns:
                conn.execute(db.text("ALTER TABLE intents ADD COLUMN ml_score FLOAT"))
            if 'ml_label' not in columns:
                conn.execute(db.text("ALTER TABLE intents ADD COLUMN ml_label VARCHAR(20)"))
            if 'risk_level' not in columns:
                conn.execute(db.text("ALTER TABLE intents ADD COLUMN risk_level VARCHAR(20)"))
            if 'decision_timestamp' not in columns:
                conn.execute(db.text("ALTER TABLE intents ADD COLUMN decision_timestamp DATETIME"))
            conn.commit()
        print("Database schema migration completed (if needed).")

def create_app():
    # Set static folder to the frontend directory
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'data', 'upi_fraud.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super_secure_32_character_secret_key_2026'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized(reason):
        return jsonify({"error": "Missing or invalid token", "details": str(reason)}), 401

    @jwt.expired_token_loader
    def expired(jwt_header, jwt_payload):
        return jsonify({"error": "Token expired"}), 401

    @jwt.invalid_token_loader
    def invalid(reason):
        return jsonify({"error": "Invalid token", "details": str(reason)}), 401
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(merchant_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(fraud_bp)
    
    with app.app_context():
        db.create_all()
        seed_users()
        # Run migration BEFORE starting services
        run_schema_migration(app)
        # Start background services only if not in testing mode
        if not app.config.get('TESTING'):
            start_timeout_scheduler(app)
        
    @app.route('/')
    def serve_index():
        return app.send_static_file('index.html')

    @app.route('/login', methods=['POST'])
    def login():
        from app.auth.jwt_utils import create_token
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            token = create_token(user.id, user.role)
            return jsonify({
                "access_token": token,
                "role": user.role,
                "user_id": user.id
            })
        
        return jsonify(msg="Invalid credentials"), 401

        
    return app

def seed_users():
    if User.query.filter_by(username='user1').first() is None:
        u1 = User(username='user1', name='John Doe', role='USER')
        u1.set_password('password123')
        db.session.add(u1)
        
        m1 = User(username='merchant1', name='Aman Store', role='MERCHANT')
        m1.set_password('password123')
        db.session.add(m1)
        
        a1 = User(username='admin1', name='Fraud Analyst', role='ADMIN')
        a1.set_password('admin123')
        db.session.add(a1)
        
        db.session.commit()
        print("Initial users seeded.")

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, use_reloader=False) # use_reloader=False to prevent thread duplication
