"""Exception classes for Atlas SDK."""

from typing import Optional


class AtlasException(Exception):
    """Base exception for all Atlas SDK errors."""

    pass


class AuthenticationError(AtlasException):
    """Raised when authentication fails."""

    pass


class APIError(AtlasException):
    """Raised when API returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, response=None):
        super().__init__(message, 404, response)


class ValidationError(AtlasException):
    """Raised when input validation fails."""

    pass
