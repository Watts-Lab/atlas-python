"""Atlas SDK - Python client for Atlas API."""

from wattslab_atlas.client import AtlasClient
from wattslab_atlas.exceptions import (
    AtlasException,
    AuthenticationError,
    APIError,
    ResourceNotFoundError,
)

__version__ = "1.2.0"
__all__ = [
    "AtlasClient",
    "AtlasException",
    "AuthenticationError",
    "APIError",
    "ResourceNotFoundError",
]
