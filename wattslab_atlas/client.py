"""Main Atlas SDK client."""

import requests
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from wattslab_atlas.auth import AuthManager
from wattslab_atlas.models import Feature, FeatureCreate, PaperList
from wattslab_atlas.exceptions import APIError, ResourceNotFoundError, ValidationError
from wattslab_atlas.storage import TokenStorage


class AtlasClient:
    """
    Atlas API client - Simple and synchronous.

    Example:
        >>> from wattslab_atlas import AtlasClient
        >>> client = AtlasClient()
        >>> client.login("user@example.com")
        >>> # Check email for magic link
        >>> client.validate_magic_link("token-from-email")
        >>> features = client.list_features()
    """

    def __init__(
        self,
        base_url: str = "https://atlas.seas.upenn.edu/api",
        timeout: int = 30,
        auto_save_token: bool = True,
    ):
        """
        Initialize Atlas client.

        Args:
            base_url: Base URL for Atlas API
            timeout: Request timeout in seconds
            auto_save_token: Whether to automatically save tokens for reuse
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        storage = TokenStorage() if auto_save_token else None
        self.auth = AuthManager(self.base_url, storage)
        self.session = requests.Session()

    def login(self, email: str, auto_login: bool = True) -> Dict[str, Any]:
        """
        Login to Atlas. Will try to use stored credentials if available.

        Args:
            email: Your email address
            auto_login: Try to use stored token if available

        Returns:
            Login response

        Example:
            >>> client.login("user@example.com")
            ✓ Using stored credentials for user@example.com
            # OR
            📧 Magic link sent to user@example.com
        """
        return self.auth.login(email, use_stored_token=auto_login)

    def validate_magic_link(self, token: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate the magic link token from your email.

        Args:
            token: The magic link token from your email
            email: Optional email (uses login email if not provided)

        Returns:
            Validation response with user info

        Example:
            >>> client.validate_magic_link("abc123...")
            ✓ Authentication successful! Token saved for future use.
        """
        return self.auth.validate_magic_link(token, email)

    def logout(self) -> Dict[str, Any]:
        """
        Logout and clear stored credentials.

        Example:
            >>> client.logout()
            ✓ Logged out successfully
        """
        return self.auth.logout()

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an authenticated request."""
        url = f"{self.base_url}{endpoint}"

        # Add authentication
        kwargs["cookies"] = self.auth.get_cookies()
        kwargs["timeout"] = self.timeout

        response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            raise APIError("Authentication required. Please login first.", 401)
        elif response.status_code == 404:
            raise ResourceNotFoundError(f"Resource not found: {endpoint}")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.text}", response.status_code)

        return response

    # ========== Features ==========

    def list_features(self, project_id: Optional[str] = None) -> List[Feature]:
        """
        List all available features.

        Args:
            project_id: Optional project ID to filter features

        Returns:
            List of Feature objects

        Example:
            >>> features = client.list_features()
            >>> for f in features:
            ...     print(f.feature_name)
        """
        params = {}
        if project_id:
            params["project_id"] = project_id

        response = self._request("GET", "/features", params=params)
        data = response.json()
        return [Feature(**f) for f in data.get("features", [])]

    def create_feature(self, feature: FeatureCreate) -> Feature:
        """
        Create a new feature.

        Args:
            feature: FeatureCreate object with feature details

        Returns:
            Created Feature object

        Example:
            >>> from wattslab_atlas.models import FeatureCreate
            >>> feature = FeatureCreate(
            ...     feature_name="Study Type",
            ...     feature_description="Type of research study",
            ...     feature_identifier="study_type"
            ... )
            >>> created = client.create_feature(feature)
        """
        response = self._request("POST", "/features", json=feature.model_dump())
        data = response.json()
        return Feature(**data["feature"])

    def delete_feature(self, feature_id: str) -> Dict[str, Any]:
        """
        Delete a feature.

        Args:
            feature_id: ID of the feature to delete

        Returns:
            Response message
        """
        response = self._request("DELETE", f"/features/{feature_id}")
        result: Dict[str, Any] = response.json()
        return result

    # ========== Papers ==========

    def list_papers(self, page: int = 1, page_size: int = 10) -> PaperList:
        """
        List your papers with pagination.

        Args:
            page: Page number (default: 1)
            page_size: Papers per page (default: 10)

        Returns:
            PaperList object with papers and pagination info

        Example:
            >>> papers = client.list_papers(page=1, page_size=5)
            >>> print(f"Total papers: {papers.total_papers}")
            >>> for paper in papers.papers:
            ...     print(paper.title or paper.file_name)
        """
        response = self._request(
            "GET", "/user/papers", params={"page": page, "page_size": page_size}
        )
        return PaperList(**response.json())

    def upload_paper(
        self, project_id: str, file_path: Union[str, Path], strategy_type: str = "assistant_api"
    ) -> Dict[str, str]:
        """
        Upload a paper to a project.

        Args:
            project_id: Project ID to add paper to
            file_path: Path to the PDF file
            strategy_type: Processing strategy (default: "assistant_api")

        Returns:
            Dictionary with filename and task ID

        Example:
            >>> result = client.upload_paper("project-123", "paper.pdf")
            >>> print(f"Task ID: {result['paper.pdf']}")
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"File not found: {path}")

        with open(path, "rb") as f:
            files = {"files[]": (path.name, f, "application/pdf")}
            data = {"project_id": project_id, "strategy_type": strategy_type}

            response = self._request("POST", "/add_paper", files=files, data=data)
            result: Dict[str, str] = response.json()
            return result

    def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a processing task.

        Args:
            task_id: Task ID to check

        Returns:
            Task status information
        """
        response = self._request("GET", "/add_paper", params={"task_id": task_id})
        result: Dict[str, Any] = response.json()
        return result

    def reprocess_paper(
        self, paper_id: str, project_id: str, strategy_type: str = "assistant_api"
    ) -> Dict[str, Any]:
        """
        Reprocess an existing paper.

        Args:
            paper_id: ID of the paper to reprocess
            project_id: Project ID
            strategy_type: Processing strategy

        Returns:
            Task information
        """
        response = self._request(
            "POST",
            f"/reprocess_paper/{paper_id}",
            json={"project_id": project_id, "strategy_type": strategy_type},
        )
        result: Dict[str, Any] = response.json()
        return result

    # ========== Projects ==========

    def get_project_features(self, project_id: str) -> List[Feature]:
        """
        Get features assigned to a project.

        Args:
            project_id: Project ID

        Returns:
            List of Feature objects
        """
        response = self._request("GET", f"/projects/{project_id}/features")
        data = response.json()
        return [Feature(**f) for f in data.get("features", [])]

    def update_project_features(self, project_id: str, feature_ids: List[str]) -> Dict[str, Any]:
        """
        Update features for a project.

        Args:
            project_id: Project ID
            feature_ids: List of feature IDs to assign

        Returns:
            Response message
        """
        response = self._request(
            "POST",
            f"/projects/{project_id}/features",
            json={"project_id": project_id, "feature_ids": feature_ids},
        )
        result: Dict[str, Any] = response.json()
        return result

    def remove_project_features(self, project_id: str, feature_ids: List[str]) -> Dict[str, Any]:
        """
        Remove features from a project.

        Args:
            project_id: Project ID
            feature_ids: List of feature IDs to remove

        Returns:
            Response message
        """
        response = self._request(
            "DELETE", f"/projects/{project_id}/features", json={"feature_ids": feature_ids}
        )
        result: Dict[str, Any] = response.json()
        return result

    def reprocess_project(
        self, project_id: str, strategy_type: str = "assistant_api"
    ) -> Dict[str, Any]:
        """
        Reprocess all papers in a project.

        Args:
            project_id: Project ID
            strategy_type: Processing strategy

        Returns:
            Dictionary with task IDs for all papers
        """
        response = self._request(
            "POST", f"/reprocess_project/{project_id}", json={"strategy_type": strategy_type}
        )
        result: Dict[str, Any] = response.json()
        return result
