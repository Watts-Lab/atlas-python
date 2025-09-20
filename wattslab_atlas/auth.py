"""Authentication handling for Atlas SDK."""

import time
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timedelta

from wattslab_atlas.exceptions import AuthenticationError
from wattslab_atlas.storage import TokenStorage


class AuthManager:
    """Manages authentication for Atlas API."""

    def __init__(self, base_url: str, storage: Optional[TokenStorage] = None):
        self.base_url = base_url
        self.storage = storage or TokenStorage()
        self.jwt_token: Optional[str] = None
        self.email: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.cookies: Dict[str, str] = {}

    def login(self, email: str, use_stored_token: bool = True) -> Dict[str, Any]:
        """
        Initiate login process or use stored token if available.

        Args:
            email: User's email address
            use_stored_token: Whether to try using a stored token first

        Returns:
            Response from login endpoint or stored credentials
        """
        self.email = email

        # Try to use stored token first
        if use_stored_token:
            stored_token = self.storage.get_token(email)
            if stored_token:
                self.jwt_token = stored_token
                self.cookies = {"jwt": stored_token}

                # Validate the stored token
                if self.check_auth():
                    print(f"✓ Using stored credentials for {email}")
                    return {"message": "Using stored credentials", "success": True}
                else:
                    # Token is invalid, remove it
                    self.storage.delete_token(email)
                    self.jwt_token = None
                    self.cookies = {}

        # Request new magic link
        try:
            response = requests.post(f"{self.base_url}/login", json={"email": email})
            response.raise_for_status()

            result: Dict[str, Any] = response.json()
            print(f"📧 Magic link sent to {email}")
            print("Check your email and run validate_magic_link() with the token")
            return result

        except requests.HTTPError as e:
            raise AuthenticationError(f"Login failed: {e.response.text}")
        except Exception as e:
            raise AuthenticationError(f"Login failed: {str(e)}")

    def validate_magic_link(self, magic_link: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate the magic link received via email.

        Args:
            magic_link: The magic link token from email
            email: Optional email (uses stored email if not provided)

        Returns:
            User information and authentication status
        """
        if not email and not self.email:
            raise AuthenticationError("Email is required for validation")

        use_email = email or self.email
        if not use_email:  # Type guard for mypy
            raise AuthenticationError("Email is required")

        try:
            response = requests.post(
                f"{self.base_url}/validate", json={"email": use_email, "magic_link": magic_link}
            )
            response.raise_for_status()

            result: Dict[str, Any] = response.json()

            # Extract JWT from cookies
            if response.cookies:
                jwt_token = response.cookies.get("jwt")
                if jwt_token:
                    self.jwt_token = jwt_token
                    self.cookies = {"jwt": jwt_token}
                    self.token_expiry = datetime.now() + timedelta(hours=48)

                    # Save token for future use
                    self.storage.save_token(use_email, jwt_token, expires_in=172800)
                    print(f"✓ Authentication successful! Token saved for future use.")

            return result

        except requests.HTTPError as e:
            if e.response.status_code == 400:
                raise AuthenticationError("Invalid or expired magic link")
            raise AuthenticationError(f"Validation failed: {e.response.text}")
        except Exception as e:
            raise AuthenticationError(f"Validation failed: {str(e)}")

    def check_auth(self) -> bool:
        """
        Check if current authentication is valid.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.jwt_token:
            return False

        try:
            response = requests.get(f"{self.base_url}/check", cookies=self.cookies)
            return bool(response.status_code == 200)
        except:
            return False

    def logout(self) -> Dict[str, Any]:
        """Logout the current user."""
        try:
            response = requests.post(f"{self.base_url}/logout", cookies=self.cookies)
            response.raise_for_status()

            # Clear stored credentials
            if self.email:
                self.storage.delete_token(self.email)

            self.jwt_token = None
            self.email = None
            self.cookies = {}

            print("✓ Logged out successfully")
            result: Dict[str, Any] = response.json()
            return result

        except Exception as e:
            raise AuthenticationError(f"Logout failed: {str(e)}")

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        return {}

    def get_cookies(self) -> Dict[str, str]:
        """Get authentication cookies for requests."""
        return self.cookies
