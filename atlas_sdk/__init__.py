"""Atlas SDK - Python client for Atlas API."""

from atlas_sdk.client import AtlasClient
from atlas_sdk.exceptions import (
    AtlasException,
    AuthenticationError,
    APIError,
    ResourceNotFoundError,
)

__version__ = "2.0.1"
__all__ = [
    "AtlasClient",
    "AtlasException",
    "AuthenticationError",
    "APIError",
    "ResourceNotFoundError",
]
