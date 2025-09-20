"""Secure token storage for Atlas SDK."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import platform

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class TokenStorage:
    """Handles secure storage of authentication tokens."""

    SERVICE_NAME = "wattslab-atlas"

    def __init__(self, use_keyring: bool = True, config_dir: Optional[Path] = None):
        """
        Initialize token storage.

        Args:
            use_keyring: Whether to use system keyring for secure storage
            config_dir: Optional custom directory for storing token file
        """
        self.use_keyring = use_keyring and KEYRING_AVAILABLE
        self.CONFIG_DIR = config_dir if config_dir is not None else Path.home() / ".atlas"
        self.TOKEN_FILE = self.CONFIG_DIR / "auth.json"

        # Ensure config directory exists
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Set appropriate permissions on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(self.CONFIG_DIR, 0o700)

    def save_token(self, email: str, token: str, expires_in: Optional[int] = None) -> None:
        """
        Save authentication token securely.

        Args:
            email: User's email address
            token: JWT token
            expires_in: Token expiration time in seconds
        """
        if self.use_keyring:
            try:
                keyring.set_password(self.SERVICE_NAME, email, token)
                # Also save metadata in file
                self._save_metadata(email, expires_in)
            except Exception:
                # Fallback to file storage
                self._save_to_file(email, token, expires_in)
        else:
            self._save_to_file(email, token, expires_in)

    def get_token(self, email: str) -> Optional[str]:
        """
        Retrieve stored token for email.

        Args:
            email: User's email address

        Returns:
            JWT token if found and valid, None otherwise
        """
        if self.use_keyring:
            try:
                token = keyring.get_password(self.SERVICE_NAME, email)
                if token:
                    return token
            except Exception:
                pass

        # Fallback to file storage
        return self._get_from_file(email)

    def delete_token(self, email: str) -> None:
        """
        Delete stored token for email.

        Args:
            email: User's email address
        """
        if self.use_keyring:
            try:
                keyring.delete_password(self.SERVICE_NAME, email)
            except Exception:
                pass

        # Also delete from file storage
        self._delete_from_file(email)

    def _save_metadata(self, email: str, expires_in: Optional[int] = None) -> None:
        """Save token metadata to file."""
        metadata = self._load_all_metadata()
        metadata[email] = {"expires_in": expires_in, "last_used": None}

        with open(self.TOKEN_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

        # Set file permissions
        if platform.system() != "Windows":
            os.chmod(self.TOKEN_FILE, 0o600)

    def _save_to_file(self, email: str, token: str, expires_in: Optional[int] = None) -> None:
        """Save token to encrypted file (fallback method)."""
        data = self._load_all_tokens()
        data[email] = {"token": token, "expires_in": expires_in}

        with open(self.TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)

        # Set file permissions
        if platform.system() != "Windows":
            os.chmod(self.TOKEN_FILE, 0o600)

    def _get_from_file(self, email: str) -> Optional[str]:
        """Get token from file storage."""
        data = self._load_all_tokens()
        if email in data:
            token = data[email].get("token")
            return token if isinstance(token, str) else None
        return None

    def _delete_from_file(self, email: str) -> None:
        """Delete token from file storage."""
        data = self._load_all_tokens()
        if email in data:
            del data[email]
            with open(self.TOKEN_FILE, "w") as f:
                json.dump(data, f, indent=2)

    def _load_all_tokens(self) -> Dict[str, Any]:
        """Load all tokens from file."""
        if not self.TOKEN_FILE.exists():
            return {}

        try:
            with open(self.TOKEN_FILE, "r") as f:
                result: Dict[str, Any] = json.load(f)
                return result
        except Exception:
            return {}

    def _load_all_metadata(self) -> Dict[str, Any]:
        """Load all metadata from file."""
        return self._load_all_tokens()
