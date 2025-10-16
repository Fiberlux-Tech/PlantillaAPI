from flask import Blueprint, request, jsonify
from .services import process_excel_file, save_transaction, get_transactions, get_transaction_details, approve_transaction, reject_transaction
from . import db

# Create a Blueprint object named 'api'
api = Blueprint('api', __name__)

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Change all decorators from @app.route to @api.route
# and remove the '/api' prefix from the URL, since the Blueprint will handle it.

@api.route('/process-excel', methods=['POST'])
def process_excel_route():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    if file and allowed_file(file.filename):
        result = process_excel_file(file)
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    else:
        return jsonify(
            {"success": False, "error": "Invalid file type. Please upload an Excel file (.xlsx, .xls)."}), 400

@api.route('/submit-transaction', methods=['POST'])
def submit_transaction_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    result = save_transaction(data)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transactions', methods=['GET'])
def get_transactions_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    result = get_transactions(page=page, per_page=per_page)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transaction/<string:transaction_id>', methods=['GET'])
def get_transaction_details_route(transaction_id):
    result = get_transaction_details(transaction_id)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 404

@api.route('/transaction/approve/<string:transaction_id>', methods=['POST'])
def approve_transaction_route(transaction_id):
    result = approve_transaction(transaction_id)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transaction/reject/<string:transaction_id>', methods=['POST'])
def reject_transaction_route(transaction_id):
    result = reject_transaction(transaction_id)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500