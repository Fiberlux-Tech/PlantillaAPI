# utils.py

from functools import wraps
from flask import jsonify
from flask_login import current_user

def admin_required(f):
    """
    Decorator that verifies the current user is authenticated and has the 'ADMIN' role.
    If unauthorized, returns a 403 Forbidden response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Checks if the user is authenticated AND has the ADMIN role
        if not current_user.is_authenticated or current_user.role != 'ADMIN':
            # 403 Forbidden: User is known but lacks necessary permission
            return jsonify({"message": "Permission denied: Admin access required."}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def finance_admin_required(f):
    """
    Decorator that checks if the current user is authenticated and has either 
    the 'FINANCE' or 'ADMIN' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Checks if the user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"message": "Authentication required."}), 401
            
        # Checks for required roles
        if current_user.role not in ['FINANCE', 'ADMIN']:
            return jsonify({"message": "Permission denied: Finance or Admin access required."}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def get_editable_categories():
    """
    Returns a list of unique categories the current user's role is authorized to edit.
    Used by the frontend to dynamically populate menus.
    """
    if not current_user.is_authenticated:
        return []
    
    # 1. Access the configuration dictionary safely via current_app
    MASTER_VARIABLE_ROLES = current_app.config['MASTER_VARIABLE_ROLES']
    
    editable_categories = set()
    user_role = current_user.role
    
    # 2. FIXED LOGIC: Ensure correct retrieval of all unique categories
    if user_role == 'ADMIN':
        # Retrieve all unique category names for the ADMIN role
        return list(set(config['category'] for config in MASTER_VARIABLE_ROLES.values()))

    # 3. Logic for other roles (FINANCE, SALES, etc.)
    for config in MASTER_VARIABLE_ROLES.values():
        if config['write_role'] == user_role:
            editable_categories.add(config['category'])
            
    return list(editable_categories)