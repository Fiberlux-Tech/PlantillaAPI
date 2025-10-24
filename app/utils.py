# app/utils.py

from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user

# --- NEW: Helper variables/functions moved from routes.py ---
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _handle_service_result(result, default_error_status=500):
    """
    Parses the result from a service function. 
    If it's a tuple (error_dict, status_code), it uses the custom status code.
    Otherwise, it assumes success (status 200) or uses the default error status.
    """
    # Check if the result is a tuple (error_dict, status_code)
    if isinstance(result, tuple) and len(result) == 2:
        error_dict, status_code = result
        return jsonify(error_dict), status_code
    
    # If not a tuple, check the 'success' key in the dictionary
    if result.get("success"):
        return jsonify(result), 200
    else:
        # Fallback for general errors (e.g., from an older service method)
        return jsonify(result), default_error_status
# -----------------------------------------------------------


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
    """
    if not current_user.is_authenticated:
        return []
    
    MASTER_VARIABLE_ROLES = current_app.config['MASTER_VARIABLE_ROLES']
    
    editable_categories = set()
    user_role = current_user.role
    
    # CRITICAL FIX: Explicitly check for 'category' using safe iteration
    if user_role == 'ADMIN':
        # Retrieve all unique category names for the ADMIN role
        return list(set(config_item.get('category') for config_item in MASTER_VARIABLE_ROLES.values() if config_item.get('category')))

    # Logic for other roles (FINANCE, SALES, etc.)
    for config_item in MASTER_VARIABLE_ROLES.values():
        if config_item.get('write_role') == user_role:
            editable_categories.add(config_item.get('category'))
            
    return list(editable_categories)