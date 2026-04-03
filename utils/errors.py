"""
Custom error classes for the finance backend API.
Each error maps to a specific HTTP status code so we can
handle them cleanly in the error handlers.
"""


class APIError(Exception):
    """Base error class for all API errors"""

    def __init__(self, message, status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        """Convert error to a dictionary for JSON response"""
        error_dict = {
            "error": self.__class__.__name__,
            "message": self.message
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class ValidationError(APIError):
    """Raised when input validation fails (400)"""

    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(APIError):
    """Raised when a resource is not found (404)"""

    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)


class ForbiddenError(APIError):
    """Raised when user doesn't have permission (403)"""

    def __init__(self, message="You don't have permission to do this"):
        super().__init__(message, status_code=403)


class UnauthorizedError(APIError):
    """Raised when authentication fails or is missing (401)"""

    def __init__(self, message="Authentication required"):
        super().__init__(message, status_code=401)


class ConflictError(APIError):
    """Raised when there's a duplicate/conflict (409)"""

    def __init__(self, message="Resource already exists"):
        super().__init__(message, status_code=409)
