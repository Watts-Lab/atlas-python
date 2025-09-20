"""Tests for data models."""

import pytest
from datetime import datetime

from wattslab_atlas.models import Feature, FeatureCreate, Paper, PaperList


class TestFeatureModel:
    """Test Feature model."""

    def test_feature_creation(self):
        """Test creating a Feature."""
        feature = Feature(
            id="feat1",
            feature_name="Test Feature",
            feature_description="Description",
            feature_identifier="test_feature",
            created_by="user",
        )

        assert feature.id == "feat1"
        assert feature.feature_name == "Test Feature"
        assert feature.feature_type == "string"
        assert feature.is_shared is False

    def test_feature_with_options(self):
        """Test Feature with enum options."""
        feature = Feature(
            id="feat2",
            feature_name="Type Feature",
            feature_description="Type selection",
            feature_identifier="type_feature",
            feature_type="enum",
            feature_enum_options=["option1", "option2"],
            created_by="user",
        )

        assert feature.feature_enum_options == ["option1", "option2"]
        assert feature.feature_type == "enum"


class TestFeatureCreateModel:
    """Test FeatureCreate model."""

    def test_feature_create_defaults(self):
        """Test FeatureCreate with defaults."""
        feature = FeatureCreate(
            feature_name="New Feature",
            feature_description="New Description",
            feature_identifier="new_feature",
        )

        assert feature.feature_name == "New Feature"
        assert feature.feature_type == "string"
        assert feature.is_shared is False
        assert feature.feature_parent is None

    def test_to_gpt_interface(self):
        """Test converting to GPT interface."""
        feature = FeatureCreate(
            feature_name="Test",
            feature_description="Test Description",
            feature_identifier="test",
            feature_type="integer",
        )

        interface = feature.to_gpt_interface()

        assert interface["type"] == "integer"
        assert interface["description"] == "Test Description"
        assert "enum" not in interface

    def test_to_gpt_interface_with_enum(self):
        """Test GPT interface with enum options."""
        feature = FeatureCreate(
            feature_name="Type",
            feature_description="Type selection",
            feature_identifier="type",
            feature_type="string",
            feature_enum_options=["A", "B", "C"],
        )

        interface = feature.to_gpt_interface()

        assert interface["enum"] == ["A", "B", "C"]


class TestPaperModel:
    """Test Paper model."""

    def test_paper_creation(self):
        """Test creating a Paper."""
        paper = Paper(
            id="paper1", title="Research Paper", file_name="research.pdf", status="processed"
        )

        assert paper.id == "paper1"
        assert paper.title == "Research Paper"
        assert paper.file_name == "research.pdf"
        assert paper.status == "processed"

    def test_paper_optional_fields(self):
        """Test Paper with optional fields."""
        paper = Paper(id="paper2")

        assert paper.id == "paper2"
        assert paper.title is None
        assert paper.file_name is None
        assert paper.status is None


class TestPaperListModel:
    """Test PaperList model."""

    def test_paper_list_creation(self):
        """Test creating a PaperList."""
        papers = [Paper(id="p1", title="Paper 1"), Paper(id="p2", title="Paper 2")]

        paper_list = PaperList(papers=papers, total_papers=50, page=1, page_size=10)

        assert len(paper_list.papers) == 2
        assert paper_list.total_papers == 50
        assert paper_list.page == 1
        assert paper_list.page_size == 10
