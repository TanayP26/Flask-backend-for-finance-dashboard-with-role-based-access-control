"""
Authentication routes - handles login and getting current user info.
"""

from flask import Blueprint, request, jsonify, g

from models import User
from middleware import authenticate_user
from utils.errors import ValidationError, UnauthorizedError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint.
    Expects JSON body with 'username' and 'password'.
    Returns user info and auth token on success.

    Example:
        POST /auth/login
        {"username": "analyst_user", "password": "analyst123"}
    """
    data = request.get_json()

    if not data:
        raise ValidationError("Request body must be JSON")

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username:
        raise ValidationError("Username is required")
    if not password:
        raise ValidationError("Password is required")

    # find the user
    user = User.get_by_username(username)

    if not user:
        raise UnauthorizedError("Invalid username or password")

    # check password (plaintext for this demo)
    if user['password_hash'] != password:
        raise UnauthorizedError("Invalid username or password")

    # check if account is active
    if user.get('status') != 'active':
        raise UnauthorizedError("Account is deactivated. Contact admin.")

    # build the token (just username:password for demo)
    auth_token = f"{username}:{password}"

    # return user info (without password obviously)
    safe_user = User.to_safe_dict(user)

    return jsonify({
        "message": "Login successful!",
        "auth_token": auth_token,
        "user": safe_user
    }), 200


@auth_bp.route('/me', methods=['GET'])
@authenticate_user
def get_me():
    """
    Get current user's profile information.
    Requires authentication.

    Example:
        GET /auth/me
        Authorization: Bearer analyst_user:analyst123
    """
    user = g.current_user
    safe_user = User.to_safe_dict(user)

    return jsonify({
        "user": safe_user
    }), 200
