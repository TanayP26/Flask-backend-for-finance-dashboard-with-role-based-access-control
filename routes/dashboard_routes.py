"""
Dashboard routes - analytics and summary endpoints.
These provide aggregated views of financial data.
"""

from flask import Blueprint, request, jsonify, g

from models import FinancialRecord, User
from middleware import authenticate_user
from utils.errors import ValidationError, NotFoundError, ForbiddenError

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def _get_target_user_id(current_user):
    """
    Figure out which user's data to show.
    Admins can pass ?user_id=X to see another user's data.
    Everyone else sees only their own data.
    """
    requested_user_id = request.args.get('user_id')

    if requested_user_id:
        if current_user['role_name'] != 'admin':
            raise ForbiddenError("Only admins can view other users' dashboards")

        try:
            target_id = int(requested_user_id)
        except ValueError:
            raise ValidationError("user_id must be a valid number")

        # make sure the user exists
        target = User.get_by_id(target_id)
        if not target:
            raise NotFoundError("User not found")

        return target_id
    else:
        # non-admin users always see their own data
        if current_user['role_name'] == 'admin':
            return None  # admin sees all data by default
        return current_user['id']


@dashboard_bp.route('/summary', methods=['GET'])
@authenticate_user
def get_summary():
    """
    Get summary statistics for financial records.

    Returns total income, total expense, net balance,
    record count, and date range.

    Query params:
        user_id (admin only) - view specific user's summary

    Example:
        GET /dashboard/summary
        GET /dashboard/summary?user_id=2  (admin only)
    """
    current_user = g.current_user
    target_user_id = _get_target_user_id(current_user)

    summary = FinancialRecord.get_summary(user_id=target_user_id)

    return jsonify({
        "summary": summary
    }), 200


@dashboard_bp.route('/category-breakdown', methods=['GET'])
@authenticate_user
def get_category_breakdown():
    """
    Get income/expense breakdown by category.

    For each category shows income total, expense total, and net.

    Query params:
        type - filter by 'income' or 'expense' (optional)
        user_id (admin only) - view specific user's data

    Example:
        GET /dashboard/category-breakdown
        GET /dashboard/category-breakdown?type=expense
    """
    current_user = g.current_user
    target_user_id = _get_target_user_id(current_user)

    record_type = request.args.get('type')
    if record_type:
        record_type = record_type.strip().lower()
        if record_type not in ('income', 'expense'):
            raise ValidationError("Type filter must be 'income' or 'expense'")

    breakdown = FinancialRecord.get_category_breakdown(
        user_id=target_user_id, record_type=record_type
    )

    return jsonify({
        "category_breakdown": breakdown,
        "total_categories": len(breakdown)
    }), 200


@dashboard_bp.route('/monthly-trend', methods=['GET'])
@authenticate_user
def get_monthly_trend():
    """
    Get monthly income/expense trend.

    Shows income, expense, net, and transaction count
    for each month.

    Query params:
        months - number of months to show (default: 12, max: 60)
        user_id (admin only) - view specific user's data

    Example:
        GET /dashboard/monthly-trend
        GET /dashboard/monthly-trend?months=6
    """
    current_user = g.current_user
    target_user_id = _get_target_user_id(current_user)

    # get months parameter
    months_param = request.args.get('months', 12)
    try:
        months = int(months_param)
    except (ValueError, TypeError):
        raise ValidationError("'months' must be a valid number")

    # clamp between 1 and 60
    if months < 1:
        months = 1
    elif months > 60:
        months = 60

    trend = FinancialRecord.get_monthly_trend(
        user_id=target_user_id, months=months
    )

    return jsonify({
        "monthly_trend": trend,
        "months_requested": months,
        "months_returned": len(trend)
    }), 200


@dashboard_bp.route('/recent-activity', methods=['GET'])
@authenticate_user
def get_recent_activity():
    """
    Get list of most recent financial records.

    Query params:
        limit - number of records to return (default: 10, max: 100)
        user_id (admin only) - view specific user's data

    Example:
        GET /dashboard/recent-activity
        GET /dashboard/recent-activity?limit=25
    """
    current_user = g.current_user
    target_user_id = _get_target_user_id(current_user)

    # get limit parameter
    limit_param = request.args.get('limit', 10)
    try:
        limit = int(limit_param)
    except (ValueError, TypeError):
        raise ValidationError("'limit' must be a valid number")

    # clamp between 1 and 100
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100

    recent = FinancialRecord.get_recent(
        user_id=target_user_id, limit=limit
    )

    return jsonify({
        "recent_activity": recent,
        "count": len(recent)
    }), 200


@dashboard_bp.route('/insights', methods=['GET'])
@authenticate_user
def get_insights():
    """
    Get analytical insights from financial data.

    Returns:
        - Highest expense category (with total)
        - Highest income source (with total)
        - Average transaction amount
        - Most active month (with transaction count)

    Query params:
        user_id (admin only) - view specific user's data

    Example:
        GET /dashboard/insights
    """
    current_user = g.current_user
    target_user_id = _get_target_user_id(current_user)

    insights = FinancialRecord.get_insights(user_id=target_user_id)

    return jsonify({
        "insights": insights
    }), 200
