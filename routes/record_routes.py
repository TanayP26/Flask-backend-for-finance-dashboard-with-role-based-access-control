"""
Financial records routes - CRUD operations for income/expense records.
Handles filtering, pagination, and access control.
"""

from flask import Blueprint, request, jsonify, g

from models import FinancialRecord, User
from middleware import authenticate_user, require_role
from database import log_audit
from utils import (
    validate_amount, validate_record_type, validate_category,
    validate_date, validate_pagination
)
from utils.errors import ValidationError, NotFoundError, ForbiddenError

record_bp = Blueprint('records', __name__, url_prefix='/records')


def _check_ownership(record, current_user):
    """
    Helper to check if user owns the record.
    Admins can access anything, others only their own.
    """
    if current_user['role_name'] == 'admin':
        return True
    if record['user_id'] != current_user['id']:
        raise ForbiddenError("You can only access your own records")
    return True


@record_bp.route('', methods=['GET'])
@authenticate_user
def list_records():
    """
    List financial records with optional filters.

    Query parameters:
        type - filter by 'income' or 'expense'
        category - filter by category name
        start_date - filter records from this date (YYYY-MM-DD)
        end_date - filter records until this date (YYYY-MM-DD)
        user_id - (admin only) filter by specific user
        page - page number (default: 1)
        per_page - records per page (default: 20, max: 100)

    Example:
        GET /records?type=income&category=Salary&page=1
    """
    current_user = g.current_user

    # get query params
    record_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    requested_user_id = request.args.get('user_id')
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)

    # validate pagination
    page, per_page = validate_pagination(page, per_page)

    # validate optional filters
    if record_type:
        record_type = validate_record_type(record_type)
    if start_date:
        start_date = validate_date(start_date)
    if end_date:
        end_date = validate_date(end_date)

    # figure out which user's records to show
    if current_user['role_name'] == 'admin':
        # admin can view any user's records
        if requested_user_id:
            try:
                target_user_id = int(requested_user_id)
            except ValueError:
                raise ValidationError("user_id must be a valid number")
            # verify the user exists
            target = User.get_by_id(target_user_id)
            if not target:
                raise NotFoundError("User not found")
            filter_user_id = target_user_id
        else:
            filter_user_id = None  # show all records
    else:
        # non-admins can only see their own records
        if requested_user_id and int(requested_user_id) != current_user['id']:
            raise ForbiddenError("You can only view your own records")
        filter_user_id = current_user['id']

    records, total = FinancialRecord.get_filtered(
        user_id=filter_user_id,
        record_type=record_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )

    return jsonify({
        "records": records,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page  # ceiling division
    }), 200


@record_bp.route('/<int:record_id>', methods=['GET'])
@authenticate_user
def get_record(record_id):
    """
    Get a single financial record by ID.
    Non-admins can only see their own records.
    """
    record = FinancialRecord.get_by_id(record_id)
    if not record:
        raise NotFoundError("Record not found")

    _check_ownership(record, g.current_user)

    return jsonify({
        "record": record
    }), 200


@record_bp.route('', methods=['POST'])
@authenticate_user
@require_role('admin', 'analyst')
def create_record():
    """
    Create a new financial record.
    Only analysts and admins can create records.
    Analysts create records for themselves.
    Admins can create records for any user.

    Expected JSON body:
        {
            "amount": 5000,
            "type": "income",
            "category": "Salary",
            "description": "Monthly salary payment",
            "record_date": "2024-01-31",
            "user_id": 2  (optional, admin only)
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body must be JSON")

    current_user = g.current_user

    # validate required fields
    amount = validate_amount(data.get('amount'))
    record_type = validate_record_type(data.get('type'))
    category = validate_category(data.get('category'))
    record_date = validate_date(data.get('record_date'))

    # description is optional
    description = data.get('description', '').strip() if data.get('description') else None

    # determine which user this record belongs to
    if 'user_id' in data and data['user_id']:
        if current_user['role_name'] != 'admin':
            raise ForbiddenError("Only admins can create records for other users")
        try:
            target_user_id = int(data['user_id'])
        except (ValueError, TypeError):
            raise ValidationError("user_id must be a valid number")
        # check target user exists
        target = User.get_by_id(target_user_id)
        if not target:
            raise NotFoundError("Target user not found")
    else:
        target_user_id = current_user['id']

    # create the record
    new_record = FinancialRecord.create(
        user_id=target_user_id,
        amount=amount,
        record_type=record_type,
        category=category,
        description=description,
        record_date=record_date
    )

    log_audit(
        current_user['id'], 'CREATE', 'financial_record',
        new_record['id'],
        f"Created {record_type} record: {category} - {amount}"
    )

    return jsonify({
        "message": "Record created successfully",
        "record": new_record
    }), 201


@record_bp.route('/<int:record_id>', methods=['PUT'])
@authenticate_user
@require_role('admin', 'analyst')
def update_record(record_id):
    """
    Update a financial record.
    Analysts can only update their own records.
    Admins can update any record.

    You can update any combination of:
        amount, type, category, description, record_date
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body must be JSON")

    # check record exists
    record = FinancialRecord.get_by_id(record_id)
    if not record:
        raise NotFoundError("Record not found")

    current_user = g.current_user

    # ownership check
    _check_ownership(record, current_user)

    # validate and collect fields to update
    update_data = {}

    if 'amount' in data:
        update_data['amount'] = validate_amount(data['amount'])

    if 'type' in data:
        update_data['type'] = validate_record_type(data['type'])

    if 'category' in data:
        update_data['category'] = validate_category(data['category'])

    if 'description' in data:
        desc = data['description']
        update_data['description'] = desc.strip() if desc else None

    if 'record_date' in data:
        update_data['record_date'] = validate_date(data['record_date'])

    if not update_data:
        raise ValidationError("No valid fields to update")

    updated_record = FinancialRecord.update(record_id, **update_data)

    log_audit(
        current_user['id'], 'UPDATE', 'financial_record',
        record_id,
        f"Updated fields: {', '.join(update_data.keys())}"
    )

    return jsonify({
        "message": "Record updated successfully",
        "record": updated_record
    }), 200


@record_bp.route('/<int:record_id>', methods=['DELETE'])
@authenticate_user
@require_role('admin', 'analyst')
def delete_record(record_id):
    """
    Soft delete a financial record.
    Doesn't actually remove it from DB, just marks it as deleted.
    Analysts can only delete their own records.
    """
    record = FinancialRecord.get_by_id(record_id)
    if not record:
        raise NotFoundError("Record not found")

    current_user = g.current_user
    _check_ownership(record, current_user)

    FinancialRecord.soft_delete(record_id)

    log_audit(
        current_user['id'], 'DELETE', 'financial_record',
        record_id,
        f"Soft deleted record: {record['category']} - {record['amount']}"
    )

    return jsonify({
        "message": "Record deleted successfully"
    }), 200


@record_bp.route('/categories', methods=['GET'])
@authenticate_user
def get_categories():
    """
    Get list of all unique categories used in records.
    Non-admins only see categories from their own records.
    """
    current_user = g.current_user

    if current_user['role_name'] == 'admin':
        categories = FinancialRecord.get_categories()
    else:
        categories = FinancialRecord.get_categories(user_id=current_user['id'])

    return jsonify({
        "categories": categories,
        "total": len(categories)
    }), 200
