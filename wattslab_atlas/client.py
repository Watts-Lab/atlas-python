"""Main Atlas SDK client."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from wattslab_atlas.auth import AuthManager
from wattslab_atlas.exceptions import APIError, ResourceNotFoundError, ValidationError
from wattslab_atlas.models import Feature, FeatureCreate, PaperList, Project
from wattslab_atlas.storage import TokenStorage

logger = logging.getLogger(__name__)


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
        token_storage_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize Atlas client.

        Args:
            base_url: Base URL for Atlas API
            timeout: Request timeout in seconds
            auto_save_token: Whether to automatically save tokens for reuse
            token_storage_path: Optional custom path for token storage file
        """
        # Log SDK version on initialization
        try:
            from wattslab_atlas import __version__

            logger.info("Atlas SDK version: %s", __version__)
        except (ImportError, AttributeError):
            logger.info("Atlas SDK version: unknown")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        storage = None
        if auto_save_token:
            config_dir = None
            if token_storage_path is not None:
                config_dir = Path(token_storage_path)
            storage = TokenStorage(config_dir=config_dir)
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
        return self.auth.login(email, use_stored_token=auto_login, is_sdk=True)

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

    def list_projects(self) -> List[Project]:
        """
        List all your projects.

        Returns:
            List of Project objects

        Example:
            >>> projects = client.list_projects()
            >>> for p in projects:
            ...     print(f"{p.title}: {len(p.papers)} papers")
        """
        response = self._request("GET", "/v1/projects/")
        data = response.json()
        return [Project(**p) for p in data.get("project", [])]

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with project details and results

        Example:
            >>> project_info = client.get_project("project-123")
            >>> print(project_info["project"]["title"])
        """
        response = self._request("GET", f"/v1/projects/{project_id}")
        result: Dict[str, Any] = response.json()
        return result

    def get_project_results(
        self, project_id: str, include_versions: bool = False
    ) -> Dict[str, Any]:
        """
        Get extraction results for a project.

        Args:
            project_id: Project ID
            include_versions: If True, includes all versions of results (default: False)

        Returns:
            Dictionary containing:
                - message: Status message
                - results: List of result dictionaries
                - ids: List of result IDs

        Example:
            >>> results = client.get_project_results("project-123")
            >>> print(f"Found {len(results['results'])} results")
            >>>
            >>> # Get all versions
            >>> all_results = client.get_project_results("project-123", include_versions=True)
        """
        params = {}
        if include_versions:
            params["include_versions"] = "true"

        response = self._request("GET", f"/v1/projects/{project_id}/results", params=params)
        result: Dict[str, Any] = response.json()
        return result

    def create_project(
        self, name: str, description: Optional[str] = None, features: Optional[List[str]] = None
    ) -> str:
        """
        Create a new project.

        Args:
            name: Project name
            description: Optional project description
            features: Optional list of feature IDs to include

        Returns:
            Project ID of created project

        Example:
            >>> project_id = client.create_project(
            ...     "My Research Project",
            ...     description="Analysis of papers",
            ...     features=["feature-id-1", "feature-id-2"]
            ... )
        """
        data: Dict[str, Any] = {
            "project_name": name,
            "project_description": description or f"Created on {datetime.now()}",
        }
        if features:
            data["project_features"] = features

        response = self._request("POST", "/v1/projects/", json=data)
        result = response.json()
        project_id: str = result["project_id"]  # Store in typed variable
        return project_id

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a project's details.

        Args:
            project_id: Project ID to update
            name: New project name (optional)
            description: New description (optional)
            prompt: New prompt (optional)

        Returns:
            Updated project information
        """
        data: Dict[str, Any] = {}
        if name:
            data["project_name"] = name
        if description:
            data["project_description"] = description
        if prompt:
            data["project_prompt"] = prompt

        response = self._request("PUT", f"/v1/projects/{project_id}", json=data)
        result: Dict[str, Any] = response.json()
        return result

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            Response message
        """
        response = self._request("DELETE", f"/v1/projects/{project_id}")
        result: Dict[str, Any] = response.json()
        return result

    def get_project_with_results(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details along with its latest results.
        Convenience method that combines project info and results.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with both project details and results

        Example:
            >>> data = client.get_project_with_results("project-123")
            >>> print(f"Project: {data['project']['title']}")
            >>> print(f"Results: {len(data['results']['results'])}")
        """
        project = self.get_project(project_id)
        results = self.get_project_results(project_id)

        return {"project": project.get("project"), "results": results}
