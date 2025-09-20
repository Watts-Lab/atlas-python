"""Tests for Atlas client."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile

from wattslab_atlas import AtlasClient, AuthenticationError, APIError, ResourceNotFoundError
from wattslab_atlas.models import Feature, FeatureCreate, Paper, PaperList


@pytest.fixture
def client():
    """Create a test client."""
    return AtlasClient(base_url="http://localhost:8080/api", auto_save_token=False)


@pytest.fixture
def auth_client(client):
    """Create an authenticated test client."""
    client.auth.jwt_token = "test-token"
    client.auth.cookies = {"jwt": "test-token"}
    client.auth.email = "test@example.com"
    return client


class TestClientInitialization:
    """Test client initialization."""

    def test_default_initialization(self):
        """Test client with default settings."""
        client = AtlasClient()
        assert client.base_url == "https://atlas.seas.upenn.edu/api"
        assert client.timeout == 30

    def test_custom_initialization(self):
        """Test client with custom settings."""
        client = AtlasClient(
            base_url="http://localhost:8080/api", timeout=60, auto_save_token=False
        )
        assert client.base_url == "http://localhost:8080/api"
        assert client.timeout == 60


class TestAuthentication:
    """Test authentication methods."""

    @patch("requests.post")
    def test_login_new_user(self, mock_post, client):
        """Test login for new user."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Magic link sent"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = client.login("test@example.com", auto_login=False)
        assert result["message"] == "Magic link sent"
        mock_post.assert_called_once_with(
            "http://localhost:8080/api/login",
            json={"email": "test@example.com", "client_type": "sdk"},
            timeout=10,
        )

    @patch("requests.post")
    def test_validate_magic_link(self, mock_post, client):
        """Test magic link validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Validated",
            "email": "test@example.com",
            "credits": 5000,
        }
        mock_response.cookies = {"jwt": "test-jwt-token"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Set email first
        client.auth.email = "test@example.com"
        result = client.validate_magic_link("magic-token-123")

        assert result["email"] == "test@example.com"
        assert client.auth.jwt_token == "test-jwt-token"

    @patch("requests.post")
    def test_logout(self, mock_post, auth_client):
        """Test logout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Logged out"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = auth_client.logout()

        assert result["message"] == "Logged out"
        assert auth_client.auth.jwt_token is None
        assert auth_client.auth.email is None


class TestFeatures:
    """Test feature-related methods."""

    @patch("requests.Session.request")
    def test_list_features(self, mock_request, auth_client):
        """Test listing features."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "id": "feat1",
                    "feature_name": "Test Feature",
                    "feature_description": "Test Description",
                    "feature_identifier": "test_feature",
                    "created_by": "user",
                }
            ]
        }
        mock_request.return_value = mock_response

        features = auth_client.list_features()

        assert len(features) == 1
        assert features[0].feature_name == "Test Feature"
        assert isinstance(features[0], Feature)

    @patch("requests.Session.request")
    def test_create_feature(self, mock_request, auth_client):
        """Test creating a feature."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "feature": {
                "id": "new-feat",
                "feature_name": "New Feature",
                "feature_description": "New Description",
                "feature_identifier": "new_feature",
                "created_by": "user",
            }
        }
        mock_request.return_value = mock_response

        new_feature = FeatureCreate(
            feature_name="New Feature",
            feature_description="New Description",
            feature_identifier="new_feature",
        )

        created = auth_client.create_feature(new_feature)

        assert created.feature_name == "New Feature"
        assert created.id == "new-feat"

    @patch("requests.Session.request")
    def test_delete_feature(self, mock_request, auth_client):
        """Test deleting a feature."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "success"}
        mock_request.return_value = mock_response

        result = auth_client.delete_feature("feat1")

        assert result["response"] == "success"
        mock_request.assert_called_once()


class TestPapers:
    """Test paper-related methods."""

    @patch("requests.Session.request")
    def test_list_papers(self, mock_request, auth_client):
        """Test listing papers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "papers": [
                {
                    "id": "paper1",
                    "title": "Test Paper",
                    "file_name": "test.pdf",
                    "status": "processed",
                }
            ],
            "total_papers": 1,
            "page": 1,
            "page_size": 10,
        }
        mock_request.return_value = mock_response

        papers = auth_client.list_papers()

        assert papers.total_papers == 1
        assert len(papers.papers) == 1
        assert papers.papers[0].title == "Test Paper"
        assert isinstance(papers, PaperList)

    @patch("requests.Session.request")
    @patch("builtins.open", new_callable=mock_open, read_data=b"PDF content")
    def test_upload_paper(self, mock_file, mock_request, auth_client):
        """Test paper upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test.pdf": "task-123"}
        mock_request.return_value = mock_response

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(b"PDF content")
            temp_path = tf.name

        try:
            result = auth_client.upload_paper("project-123", temp_path)
            assert "task-123" in str(result.values())
        finally:
            Path(temp_path).unlink()

    @patch("requests.Session.request")
    def test_check_task_status(self, mock_request, auth_client):
        """Test checking task status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "result": "success"}
        mock_request.return_value = mock_response

        status = auth_client.check_task_status("task-123")

        assert status["status"] == "completed"
        assert status["result"] == "success"


class TestProjects:
    """Test project-related methods."""

    @patch("requests.Session.request")
    def test_get_project_features(self, mock_request, auth_client):
        """Test getting project features."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "id": "feat1",
                    "feature_name": "Project Feature",
                    "feature_description": "Description",
                    "feature_identifier": "proj_feature",
                    "created_by": "user",
                }
            ]
        }
        mock_request.return_value = mock_response

        features = auth_client.get_project_features("project-123")

        assert len(features) == 1
        assert features[0].feature_name == "Project Feature"

    @patch("requests.Session.request")
    def test_update_project_features(self, mock_request, auth_client):
        """Test updating project features."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"message": "Features updated"}
        mock_request.return_value = mock_response

        result = auth_client.update_project_features("project-123", ["feat1", "feat2"])

        assert result["message"] == "Features updated"

    @patch("requests.Session.request")
    def test_reprocess_project(self, mock_request, auth_client):
        """Test reprocessing project."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Started reprocessing",
            "total_papers": 5,
            "task_ids": {"paper1": "task1", "paper2": "task2"},
        }
        mock_request.return_value = mock_response

        result = auth_client.reprocess_project("project-123")

        assert result["total_papers"] == 5
        assert "task_ids" in result


class TestErrorHandling:
    """Test error handling."""

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request, client):
        """Test authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.list_features()

        assert "Authentication required" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    @patch("requests.Session.request")
    def test_not_found_error(self, mock_request, auth_client):
        """Test resource not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_request.return_value = mock_response

        with pytest.raises(ResourceNotFoundError) as exc_info:
            auth_client.delete_feature("nonexistent")

        assert "Resource not found" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_general_api_error(self, mock_request, auth_client):
        """Test general API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            auth_client.list_features()

        assert "API error" in str(exc_info.value)
        assert exc_info.value.status_code == 500
