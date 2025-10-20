# auth.py

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from .models import User, db 
from werkzeug.security import generate_password_hash

# Define the Blueprint
bp = Blueprint('auth', __name__)

# --- Helper Function for Initial Setup (Use ONCE to create Admin/Finance users) ---
@bp.route('/setup/create_default_users', methods=['POST'])
def create_default_users():
    """
    Endpoint to create initial users. SHOULD BE DELETED OR SECURED IN PRODUCTION.
    Run this ONLY once after 'flask db upgrade'.
    """
    if User.query.count() > 0:
        return jsonify({"message": "Users already exist. Setup skipped."}), 200

    admin = User(username='admin', email='admin@app.com', role='ADMIN')
    admin.set_password('adminpass') 
    
    finance = User(username='finance', email='finance@app.com', role='FINANCE')
    finance.set_password('financepass')

    sales = User(username='salesrep', email='sales@app.com', role='SALES')
    sales.set_password('salespass')
    
    db.session.add_all([admin, finance, sales])
    db.session.commit()

    return jsonify({"message": "Default users created successfully."}), 201
# ---------------------------------------------------


@bp.route('/register', methods=['POST'])
def register():
    """Creates a new user account with the default 'SALES' role."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Missing username, email, or password"}), 400

    # Check for existing user
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already taken"}), 409
    
    # Check for existing email
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    try:
        new_user = User(username=username, email=email, role='SALES')
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in automatically after registration
        login_user(new_user)

        return jsonify({
            "message": "Registration successful. Logged in as SALES.",
            "username": new_user.username,
            "role": new_user.role
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred during registration: {str(e)}"}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Authenticates a user and starts a session."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        return jsonify({"message": "Invalid username or password"}), 401

    login_user(user)
    # Return user details needed by the frontend for state/role management
    return jsonify({
        "message": "Login successful",
        "username": user.username,
        "role": user.role
    }), 200

@bp.route('/logout', methods=['POST'])
@login_required 
def logout():
    """Ends the user session."""
    logout_user()
    return jsonify({"message": "Successfully logged out"}), 200

@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Returns the current user's profile information."""
    return jsonify({
        "is_authenticated": True,
        "username": current_user.username,
        "role": current_user.role
    }), 200
