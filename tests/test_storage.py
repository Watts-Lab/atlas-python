"""Tests for token storage module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from wattslab_atlas.storage import TokenStorage


class TestTokenStorage:
    """Test TokenStorage class."""

    @patch("pathlib.Path.mkdir")
    def test_initialization(self, mock_mkdir):
        """Test storage initialization."""
        storage = TokenStorage(use_keyring=False)

        assert storage.SERVICE_NAME == "wattslab-atlas"
        mock_mkdir.assert_called_once()

    @patch("keyring.set_password")
    @patch("wattslab_atlas.storage.KEYRING_AVAILABLE", True)
    def test_save_token_with_keyring(self, mock_set_password):
        """Test saving token with keyring."""
        storage = TokenStorage(use_keyring=True)

        with patch.object(storage, "_save_metadata") as mock_metadata:
            storage.save_token("test@example.com", "test-token", 3600)

            mock_set_password.assert_called_once_with(
                "wattslab-atlas", "test@example.com", "test-token"
            )
            mock_metadata.assert_called_once()

    @patch("wattslab_atlas.storage.KEYRING_AVAILABLE", False)
    def test_save_token_without_keyring(self):
        """Test saving token without keyring."""
        storage = TokenStorage(use_keyring=False)

        with patch.object(storage, "_save_to_file") as mock_save:
            storage.save_token("test@example.com", "test-token", 3600)

            mock_save.assert_called_once_with("test@example.com", "test-token", 3600)

    @patch("keyring.get_password")
    @patch("wattslab_atlas.storage.KEYRING_AVAILABLE", True)
    def test_get_token_with_keyring(self, mock_get_password):
        """Test getting token with keyring."""
        mock_get_password.return_value = "stored-token"

        storage = TokenStorage(use_keyring=True)
        token = storage.get_token("test@example.com")

        assert token == "stored-token"
        mock_get_password.assert_called_once()

    def test_get_token_from_file(self):
        """Test getting token from file."""
        storage = TokenStorage(use_keyring=False)

        test_data = {"test@example.com": {"token": "file-token", "expires_in": 3600}}

        with patch.object(storage, "_load_all_tokens", return_value=test_data):
            token = storage.get_token("test@example.com")

            assert token == "file-token"

    @patch("keyring.delete_password")
    @patch("wattslab_atlas.storage.KEYRING_AVAILABLE", True)
    def test_delete_token(self, mock_delete_password):
        """Test deleting token."""
        storage = TokenStorage(use_keyring=True)

        with patch.object(storage, "_delete_from_file") as mock_delete_file:
            storage.delete_token("test@example.com")

            mock_delete_password.assert_called_once()
            mock_delete_file.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_load_all_tokens_file_not_exists(self, mock_exists):
        """Test loading tokens when file doesn't exist."""
        mock_exists.return_value = False
        storage = TokenStorage(use_keyring=False)

        data = storage._load_all_tokens()

        assert data == {}
        mock_exists.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_all_tokens_file_exists(self, mock_file, mock_exists):
        """Test loading tokens from existing file."""
        mock_exists.return_value = True
        test_data = {"test@example.com": {"token": "test"}}
        mock_file.return_value.read.return_value = json.dumps(test_data)

        # Configure mock_open properly
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(test_data)

        storage = TokenStorage(use_keyring=False)

        with patch("json.load", return_value=test_data):
            data = storage._load_all_tokens()

            assert data == test_data

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    def test_save_to_file(self, mock_chmod, mock_file):
        """Test saving token to file."""
        storage = TokenStorage(use_keyring=False)

        with patch.object(storage, "_load_all_tokens", return_value={}):
            with patch("json.dump") as mock_dump:
                storage._save_to_file("test@example.com", "token123", 3600)

                mock_dump.assert_called_once()
                call_args = mock_dump.call_args[0][0]
                assert "test@example.com" in call_args
                assert call_args["test@example.com"]["token"] == "token123"

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    def test_save_metadata(self, mock_chmod, mock_file):
        """Test saving metadata."""
        storage = TokenStorage(use_keyring=False)

        with patch.object(storage, "_load_all_metadata", return_value={}):
            with patch("json.dump") as mock_dump:
                storage._save_metadata("test@example.com", 3600)

                mock_dump.assert_called_once()
                call_args = mock_dump.call_args[0][0]
                assert "test@example.com" in call_args
                assert call_args["test@example.com"]["expires_in"] == 3600

    @patch("builtins.open", new_callable=mock_open)
    def test_delete_from_file(self, mock_file):
        """Test deleting token from file."""
        storage = TokenStorage(use_keyring=False)

        existing_data = {
            "test@example.com": {"token": "token123"},
            "other@example.com": {"token": "token456"},
        }

        with patch.object(storage, "_load_all_tokens", return_value=existing_data):
            with patch("json.dump") as mock_dump:
                storage._delete_from_file("test@example.com")

                mock_dump.assert_called_once()
                call_args = mock_dump.call_args[0][0]
                assert "test@example.com" not in call_args
                assert "other@example.com" in call_args

    def test_get_from_file_not_found(self):
        """Test getting non-existent token from file."""
        storage = TokenStorage(use_keyring=False)

        with patch.object(storage, "_load_all_tokens", return_value={}):
            token = storage._get_from_file("nonexistent@example.com")

            assert token is None

    def test_get_from_file_invalid_data(self):
        """Test getting token with invalid data structure."""
        storage = TokenStorage(use_keyring=False)

        # Missing 'token' key
        test_data = {"test@example.com": {"expires_in": 3600}}

        with patch.object(storage, "_load_all_tokens", return_value=test_data):
            token = storage._get_from_file("test@example.com")

            assert token is None
