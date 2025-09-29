"""Enhanced data models for Atlas SDK with auto-loading capabilities."""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Avoid circular import for type checking
if TYPE_CHECKING:
    from wattslab_atlas.client import AtlasClient


class Feature(BaseModel):
    """Feature model."""

    id: str
    feature_name: str
    feature_description: str
    feature_identifier: str
    feature_type: Optional[str] = "string"
    feature_prompt: Optional[str] = None
    feature_enum_options: Optional[List[str]] = Field(default_factory=list)
    is_shared: bool = False
    created_by: str


class FeatureCreate(BaseModel):
    """Model for creating a new feature."""

    feature_name: str
    feature_description: str
    feature_identifier: str
    feature_parent: Optional[str] = None
    feature_type: str = "string"
    feature_enum_options: Optional[List[str]] = Field(default_factory=list)
    is_shared: bool = False

    def to_gpt_interface(self) -> Dict[str, Any]:
        """Convert to GPT interface format."""
        interface: Dict[str, Any] = {
            "type": self.feature_type,
            "description": self.feature_description,
        }
        if self.feature_enum_options:
            interface["enum"] = self.feature_enum_options
        return interface


class Paper(BaseModel):
    """Paper model."""

    id: str
    title: Optional[str] = None
    file_name: Optional[str] = None
    status: Optional[str] = None


class PaperList(BaseModel):
    """Paginated paper list response."""

    papers: List[Paper]
    total_papers: int
    page: int
    page_size: int


class ProcessingTask(BaseModel):
    """Processing task result."""

    task_id: str
    paper_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class Project(BaseModel):
    """
    Project model with auto-loading capabilities.

    Example:
        >>> # Create from existing data
        >>> project = Project(id="proj-123", title="My Project", ...)
        >>>
        >>> # Or load from ID
        >>> project = Project.from_id("proj-123", client)
        >>> print(project.title)
        >>>
        >>> # Refresh data
        >>> project.refresh()
        >>>
        >>> # Load results
        >>> results = project.get_results()
    """

    id: str
    title: str
    description: str
    updated_at: datetime
    papers: List[str] = Field(default_factory=list)
    results: Optional[List[Dict[str, Any]]] = None

    # Store client reference (not serialized)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _client: Optional["AtlasClient"] = None

    @classmethod
    def from_id(cls, project_id: str, client: "AtlasClient") -> "Project":
        """
        Load a project by ID.

        Args:
            project_id: The project ID to load
            client: AtlasClient instance

        Returns:
            Project instance with loaded data

        Example:
            >>> from wattslab_atlas import AtlasClient
            >>> client = AtlasClient()
            >>> client.login("user@example.com")
            >>> project = Project.from_id("proj-123", client)
        """
        data = client.get_project(project_id)
        project_data = data.get("project", {})
        project = cls(**project_data)
        project._client = client
        return project

    def refresh(self) -> None:
        """
        Refresh project data from the server.

        Raises:
            ValueError: If no client is attached

        Example:
            >>> project.refresh()
            >>> print(f"Updated at: {project.updated_at}")
        """
        if not self._client:
            raise ValueError("No client attached. Use Project.from_id() or attach_client() first.")

        data = self._client.get_project(self.id)
        project_data = data.get("project", {})

        # Update all fields
        for key, value in project_data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_results(self, include_versions: bool = False) -> Dict[str, Any]:
        """
        Get extraction results for this project.

        Args:
            include_versions: If True, includes all versions of results

        Returns:
            Dictionary with results data

        Raises:
            ValueError: If no client is attached

        Example:
            >>> results = project.get_results()
            >>> print(f"Found {len(results['results'])} results")
        """
        if not self._client:
            raise ValueError("No client attached. Use Project.from_id() or attach_client() first.")

        return self._client.get_project_results(self.id, include_versions)

    def get_features(self) -> List[Feature]:
        """
        Get features assigned to this project.

        Returns:
            List of Feature objects

        Raises:
            ValueError: If no client is attached
        """
        if not self._client:
            raise ValueError("No client attached. Use Project.from_id() or attach_client() first.")

        return self._client.get_project_features(self.id)

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> None:
        """
        Update project details and refresh.

        Args:
            name: New project name
            description: New description
            prompt: New prompt

        Raises:
            ValueError: If no client is attached

        Example:
            >>> project.update(name="Updated Name", description="New description")
        """
        if not self._client:
            raise ValueError("No client attached. Use Project.from_id() or attach_client() first.")

        self._client.update_project(self.id, name, description, prompt)
        self.refresh()

    def delete(self) -> Dict[str, Any]:
        """
        Delete this project.

        Returns:
            Response message

        Raises:
            ValueError: If no client is attached

        Example:
            >>> response = project.delete()
            >>> print(response['message'])
        """
        if not self._client:
            raise ValueError("No client attached. Use Project.from_id() or attach_client() first.")

        return self._client.delete_project(self.id)

    def attach_client(self, client: "AtlasClient") -> None:
        """
        Attach a client to enable API operations.

        Args:
            client: AtlasClient instance

        Example:
            >>> project = Project(id="proj-123", title="My Project", ...)
            >>> project.attach_client(client)
            >>> project.refresh()
        """
        self._client = client


class ProjectList(BaseModel):
    """Project list response."""

    project: List[Project]


class ProjectResult(BaseModel):
    """Minimal result model for project results."""

    created_at: Optional[str] = None
    _version: int = 1
    is_latest: bool = True
    result_id: str
    paper_id: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class ProjectResultsResponse(BaseModel):
    """Response for project results endpoint."""

    message: str
    results: List[Dict[str, Any]]
    ids: List[str]
