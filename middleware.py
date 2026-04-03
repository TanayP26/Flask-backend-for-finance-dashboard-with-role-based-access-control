"""
Middleware for handling authentication and authorization.
Contains decorators that we use on route functions to check
if the user is logged in and has the right permissions.
"""

import base64
from functools import wraps
from flask import request, g

from models import User
from utils.errors import UnauthorizedError, ForbiddenError


def authenticate_user(f):
    """
    Decorator to check if the user is authenticated.
    Looks for the Authorization header with format:
        Authorization: Bearer username:password

    If valid, sets g.current_user to the user dict so
    other parts of the code can access it easily.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            raise UnauthorizedError("Missing Authorization header. Please login first.")

        # check format - should start with 'Bearer '
        parts = auth_header.split(' ', 1)
        if len(parts) != 2 or parts[0] != 'Bearer':
            raise UnauthorizedError("Invalid authorization format. Use: Bearer username:password")

        token = parts[1]

        # token is username:password
        if ':' not in token:
            raise UnauthorizedError("Invalid token format")

        # split only on first colon (password might contain colons)
        username, password = token.split(':', 1)

        if not username or not password:
            raise UnauthorizedError("Username and password cannot be empty")

        # look up the user
        user = User.get_by_username(username)
        if not user:
            raise UnauthorizedError("Invalid credentials")

        # check password (plaintext comparison for demo)
        if user['password_hash'] != password:
            raise UnauthorizedError("Invalid credentials")

        # check if user account is active
        if user.get('status') != 'active':
            raise UnauthorizedError("Your account has been deactivated")

        # store user info for use in route handlers
        g.current_user = user

        return f(*args, **kwargs)

    return decorated


def require_role(*allowed_roles):
    """
    Decorator to restrict access based on user role.
    Must be used AFTER @authenticate_user so g.current_user exists.

    Usage example:
        @authenticate_user
        @require_role('admin', 'analyst')
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = getattr(g, 'current_user', None)
            if not current_user:
                raise UnauthorizedError("Authentication required")

            user_role = current_user.get('role_name', '')

            if user_role not in allowed_roles:
                raise ForbiddenError(
                    f"Access denied. Required role: {', '.join(allowed_roles)}. "
                    f"Your role: {user_role}"
                )

            return f(*args, **kwargs)

        return decorated
    return decorator


def check_record_ownership(f):
    """
    Decorator to check if the user owns the record they're trying
    to access/modify. Admins bypass this check.
    Must be used after @authenticate_user.

    Expects 'record_id' in the URL parameters.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            raise UnauthorizedError("Authentication required")

        # admins can access any record
        if current_user['role_name'] == 'admin':
            return f(*args, **kwargs)

        # for non-admins, we'll check ownership inside the route
        # because we need the record data which the route fetches anyway
        # so we just let it through here and the route handles the check
        return f(*args, **kwargs)

    return decorated


def get_current_user():
    """
    Helper function to get the current logged-in user.
    Returns None if nobody is logged in.
    """
    return getattr(g, 'current_user', None)


def is_admin():
    """Quick check if current user is an admin"""
    user = get_current_user()
    return user and user.get('role_name') == 'admin'


def is_analyst():
    """Quick check if current user is an analyst"""
    user = get_current_user()
    return user and user.get('role_name') == 'analyst'


def is_viewer():
    """Quick check if current user is a viewer"""
    user = get_current_user()
    return user and user.get('role_name') == 'viewer'
