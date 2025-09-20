"""Data models for Atlas SDK."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


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
    """Project model."""

    id: str
    title: str
    description: str
    updated_at: datetime
    papers: List[str] = Field(default_factory=list)
    results: Optional[List[Dict[str, Any]]] = None


class ProjectList(BaseModel):
    """Project list response."""

    project: List[Project]


class ProjectResult(BaseModel):
    """Minimal result model for project results."""

    created_at: Optional[str] = None
    _version: int = 1
    _is_latest: bool = True
    _result_id: str
    _paper_id: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ProjectResultsResponse(BaseModel):
    """Response for project results endpoint."""

    message: str
    results: List[Dict[str, Any]]
    ids: List[str]
