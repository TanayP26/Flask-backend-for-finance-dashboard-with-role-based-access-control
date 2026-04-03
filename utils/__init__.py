"""
Validation utility functions for the finance backend.
All input validation is done here so the route handlers stay clean.
"""

import re
from datetime import datetime
from .errors import ValidationError


def validate_username(username):
    """
    Username must be 3-50 characters, only letters, numbers,
    underscores and hyphens allowed.
    """
    if not username or not isinstance(username, str):
        raise ValidationError("Username is required")

    username = username.strip()
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")
    if len(username) > 50:
        raise ValidationError("Username cannot be more than 50 characters")

    # only allow alphanumeric, underscore, hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscores and hyphens"
        )

    return username


def validate_email(email):
    """
    Check if email looks valid. Not super strict but
    catches the obvious bad ones.
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required")

    email = email.strip().lower()

    # basic email pattern check
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Please provide a valid email address")

    if len(email) > 120:
        raise ValidationError("Email is too long (max 120 characters)")

    return email


def validate_password(password):
    """Password must be at least 6 characters"""
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required")

    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long")

    if len(password) > 128:
        raise ValidationError("Password is too long")

    return password


def validate_amount(amount):
    """
    Amount should be a positive number and not crazy large.
    Returns the amount as a float.
    """
    if amount is None:
        raise ValidationError("Amount is required")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValidationError("Amount must be a valid number")

    if amount <= 0:
        raise ValidationError("Amount must be greater than zero")

    if amount > 999999999.99:
        raise ValidationError("Amount is too large")

    # round to 2 decimal places
    return round(amount, 2)


def validate_record_type(record_type):
    """Record type must be either 'income' or 'expense'"""
    if not record_type or not isinstance(record_type, str):
        raise ValidationError("Record type is required")

    record_type = record_type.strip().lower()
    if record_type not in ('income', 'expense'):
        raise ValidationError("Record type must be 'income' or 'expense'")

    return record_type


def validate_category(category):
    """Category should be 2-50 characters"""
    if not category or not isinstance(category, str):
        raise ValidationError("Category is required")

    category = category.strip()
    if len(category) < 2:
        raise ValidationError("Category must be at least 2 characters")
    if len(category) > 50:
        raise ValidationError("Category cannot be more than 50 characters")

    return category


def validate_date(date_str):
    """
    Validate date string in YYYY-MM-DD format.
    Returns the validated date string.
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError("Date is required")

    date_str = date_str.strip()
    try:
        parsed = datetime.strptime(date_str, '%Y-%m-%d')
        return parsed.strftime('%Y-%m-%d')
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format (e.g. 2024-01-15)")


def validate_role(role):
    """Role must be one of the predefined roles"""
    if not role or not isinstance(role, str):
        raise ValidationError("Role is required")

    role = role.strip().lower()
    valid_roles = ('viewer', 'analyst', 'admin')
    if role not in valid_roles:
        raise ValidationError(f"Role must be one of: {', '.join(valid_roles)}")

    return role


def validate_status(status):
    """Status must be active or inactive"""
    if not status or not isinstance(status, str):
        raise ValidationError("Status is required")

    status = status.strip().lower()
    if status not in ('active', 'inactive'):
        raise ValidationError("Status must be 'active' or 'inactive'")

    return status


def validate_pagination(page, per_page):
    """
    Validate and return pagination parameters.
    Returns (page, per_page) as integers.
    """
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 20
    except (ValueError, TypeError):
        raise ValidationError("Page and per_page must be valid numbers")

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > 100:
        per_page = 100

    return page, per_page
