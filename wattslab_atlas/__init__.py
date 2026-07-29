"""Atlas SDK - Python client for Atlas API."""

from wattslab_atlas.client import AtlasClient
from wattslab_atlas.exceptions import (
    AtlasException,
    AuthenticationError,
    APIError,
    ResourceNotFoundError,
)
from wattslab_atlas.models import AVAILABLE_MODELS, ProjectLLM

__version__ = "1.3.1"
__all__ = [
    "AtlasClient",
    "AtlasException",
    "AuthenticationError",
    "APIError",
    "ResourceNotFoundError",
    "ProjectLLM",
    "AVAILABLE_MODELS",
]
