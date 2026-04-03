"""
User management routes - CRUD operations for user accounts.
Most of these are admin-only except listing (analyst can also list).
"""

from flask import Blueprint, request, jsonify, g

from models import User, Role
from middleware import authenticate_user, require_role
from database import log_audit
from utils import (
    validate_username, validate_email, validate_password,
    validate_role, validate_status
)
from utils.errors import ValidationError, NotFoundError, ForbiddenError

user_bp = Blueprint('users', __name__, url_prefix='/users')


@user_bp.route('', methods=['GET'])
@authenticate_user
@require_role('admin', 'analyst')
def list_users():
    """
    Get list of all users.
    Only admins and analysts can see the user list.

    Example:
        GET /users
        Authorization: Bearer admin_user:admin123
    """
    users = User.get_all()

    # remove password hashes from response
    safe_users = [User.to_safe_dict(u) for u in users]

    return jsonify({
        "users": safe_users,
        "total": len(safe_users)
    }), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
@authenticate_user
def get_user(user_id):
    """
    Get details of a specific user.
    Any authenticated user can view user profiles.

    Example:
        GET /users/2
    """
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    safe_user = User.to_safe_dict(user)

    return jsonify({
        "user": safe_user
    }), 200


@user_bp.route('', methods=['POST'])
@authenticate_user
@require_role('admin')
def create_user():
    """
    Create a new user account.
    Admin only.

    Expected JSON body:
        {
            "username": "new_user",
            "email": "user@example.com",
            "password": "password123",
            "role": "analyst"  (or viewer/admin)
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body must be JSON")

    # validate all fields
    username = validate_username(data.get('username'))
    email = validate_email(data.get('email'))
    password = validate_password(data.get('password'))
    role_name = validate_role(data.get('role', 'viewer'))

    # get the role id
    role = Role.get_by_name(role_name)
    if not role:
        raise ValidationError(f"Role '{role_name}' does not exist")

    # create the user
    new_user = User.create(username, email, password, role['id'])

    # log the action
    log_audit(
        g.current_user['id'], 'CREATE', 'user',
        new_user['id'], f"Created user: {username}"
    )

    safe_user = User.to_safe_dict(new_user)

    return jsonify({
        "message": f"User '{username}' created successfully",
        "user": safe_user
    }), 201


@user_bp.route('/<int:user_id>', methods=['PUT'])
@authenticate_user
@require_role('admin')
def update_user(user_id):
    """
    Update a user's information.
    Admin only.

    You can update any combination of these fields:
        username, email, password, role, status
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body must be JSON")

    # check user exists
    existing_user = User.get_by_id(user_id)
    if not existing_user:
        raise NotFoundError("User not found")

    # validate and collect update fields
    update_data = {}

    if 'username' in data:
        update_data['username'] = validate_username(data['username'])

    if 'email' in data:
        update_data['email'] = validate_email(data['email'])

    if 'password' in data:
        update_data['password'] = validate_password(data['password'])

    if 'role' in data:
        role_name = validate_role(data['role'])
        role = Role.get_by_name(role_name)
        if not role:
            raise ValidationError(f"Role '{role_name}' does not exist")
        update_data['role_id'] = role['id']

    if 'status' in data:
        update_data['status'] = validate_status(data['status'])

    if not update_data:
        raise ValidationError("No valid fields to update")

    # do the update
    updated_user = User.update(user_id, **update_data)

    log_audit(
        g.current_user['id'], 'UPDATE', 'user',
        user_id, f"Updated user fields: {', '.join(update_data.keys())}"
    )

    safe_user = User.to_safe_dict(updated_user)

    return jsonify({
        "message": "User updated successfully",
        "user": safe_user
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@authenticate_user
@require_role('admin')
def delete_user(user_id):
    """
    Delete a user account.
    Admin only. Cannot delete yourself.
    """
    # don't allow deleting yourself
    if g.current_user['id'] == user_id:
        raise ForbiddenError("You cannot delete your own account")

    existing = User.get_by_id(user_id)
    if not existing:
        raise NotFoundError("User not found")

    User.delete(user_id)

    log_audit(
        g.current_user['id'], 'DELETE', 'user',
        user_id, f"Deleted user: {existing['username']}"
    )

    return jsonify({
        "message": f"User '{existing['username']}' has been deleted"
    }), 200
