"""Tests for authentication module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from wattslab_atlas.auth import AuthManager
from wattslab_atlas.storage import TokenStorage
from wattslab_atlas.exceptions import AuthenticationError


@pytest.fixture
def auth_manager():
    """Create an auth manager for testing."""
    return AuthManager(base_url="http://localhost:8080/api")


class TestAuthManager:
    """Test AuthManager class."""

    @patch("requests.post")
    def test_login_request_magic_link(self, mock_post, auth_manager):
        """Test requesting a magic link."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Magic link sent"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = auth_manager.login("test@example.com", use_stored_token=False)

        assert result["message"] == "Magic link sent"
        assert auth_manager.email == "test@example.com"

    @patch("requests.get")
    @patch.object(TokenStorage, "get_token")
    def test_login_with_stored_token(self, mock_get_token, mock_get, auth_manager):
        """Test login with stored token."""
        mock_get_token.return_value = "stored-token"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = auth_manager.login("test@example.com", use_stored_token=True)

        assert result["success"] is True
        assert auth_manager.jwt_token == "stored-token"

    @patch("requests.post")
    def test_validate_magic_link_success(self, mock_post, auth_manager):
        """Test successful magic link validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Validated",
            "email": "test@example.com",
            "credits": 5000,
        }
        mock_response.cookies = {"jwt": "new-token"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        auth_manager.email = "test@example.com"

        with patch.object(auth_manager.storage, "save_token") as mock_save:
            result = auth_manager.validate_magic_link("magic-link-123")

            assert result["email"] == "test@example.com"
            assert auth_manager.jwt_token == "new-token"
            mock_save.assert_called_once()

    def test_validate_magic_link_no_email(self, auth_manager):
        """Test validation without email."""
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.validate_magic_link("magic-link-123")

        assert "Email is required" in str(exc_info.value)

    @patch("requests.get")
    def test_check_auth_valid(self, mock_get, auth_manager):
        """Test checking valid authentication."""
        auth_manager.jwt_token = "valid-token"
        auth_manager.cookies = {"jwt": "valid-token"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert auth_manager.check_auth() is True

    def test_check_auth_no_token(self, auth_manager):
        """Test checking auth with no token."""
        assert auth_manager.check_auth() is False

    @patch("requests.post")
    def test_logout(self, mock_post, auth_manager):
        """Test logout."""
        auth_manager.jwt_token = "token"
        auth_manager.email = "test@example.com"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Logged out"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with patch.object(auth_manager.storage, "delete_token") as mock_delete:
            result = auth_manager.logout()

            assert result["message"] == "Logged out"
            assert auth_manager.jwt_token is None
            assert auth_manager.email is None
            mock_delete.assert_called_once_with("test@example.com")
