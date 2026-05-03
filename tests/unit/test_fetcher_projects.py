"""Unit tests for staticmine.fetcher.projects."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from staticmine.fetcher.projects import fetch_projects

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_mock_project(
    id: int,
    identifier: str,
    name: str,
    description: str,
    is_public: bool,
    created_on: str,
    updated_on: str,
    parent_id: int | None = None,
) -> MagicMock:
    """Create a mock Redmine project resource."""
    project = MagicMock()
    project.id = id
    project.identifier = identifier
    project.name = name
    project.description = description
    project.is_public = is_public
    project.created_on = created_on
    project.updated_on = updated_on
    if parent_id is not None:
        parent = MagicMock()
        parent.id = parent_id
        project.parent = parent
    else:
        project.parent = None
    return project


class TestFetchProjects:
    """Tests for fetch_projects function."""

    def test_fetch_projects_writes_json_file(self, tmp_path: Path) -> None:
        """fetch_projects should create raw/projects.json with correct data."""
        mock_projects = [
            _make_mock_project(
                1,
                "alpha",
                "Alpha Project",
                "Desc",
                True,
                "2021-01-01T00:00:00Z",
                "2021-06-01T00:00:00Z",
            ),
            _make_mock_project(
                2,
                "beta",
                "Beta Project",
                "Desc2",
                False,
                "2022-03-15T09:00:00Z",
                "2023-01-20T12:00:00Z",
            ),
        ]

        with patch("staticmine.fetcher.projects.Redmine") as mock_redmine_cls:
            mock_redmine = MagicMock()
            mock_redmine_cls.return_value = mock_redmine
            mock_redmine.project.all.return_value = mock_projects

            raw_dir = tmp_path / "raw"
            fetch_projects("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects.json"
        assert output_path.exists(), "projects.json should be created"

        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["identifier"] == "alpha"
        assert data[0]["name"] == "Alpha Project"
        assert data[0]["is_public"] is True
        assert data[1]["identifier"] == "beta"
        assert data[1]["is_public"] is False

    def test_fetch_projects_includes_parent_id_when_present(self, tmp_path: Path) -> None:
        """fetch_projects should include parent_id if the project has a parent."""
        mock_projects = [
            _make_mock_project(
                3,
                "gamma",
                "Gamma Sub",
                "Sub-project",
                True,
                "2023-05-10T08:30:00Z",
                "2023-05-10T08:30:00Z",
                parent_id=1,
            ),
        ]

        with patch("staticmine.fetcher.projects.Redmine") as mock_redmine_cls:
            mock_redmine = MagicMock()
            mock_redmine_cls.return_value = mock_redmine
            mock_redmine.project.all.return_value = mock_projects

            raw_dir = tmp_path / "raw"
            fetch_projects("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects.json"
        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert data[0]["parent_id"] == 1

    def test_fetch_projects_creates_raw_dir_if_missing(self, tmp_path: Path) -> None:
        """fetch_projects should create the raw directory if it does not exist."""
        with patch("staticmine.fetcher.projects.Redmine") as mock_redmine_cls:
            mock_redmine = MagicMock()
            mock_redmine_cls.return_value = mock_redmine
            mock_redmine.project.all.return_value = []

            raw_dir = tmp_path / "deep" / "raw"
            assert not raw_dir.exists()
            fetch_projects("https://redmine.example.com", "test-key", raw_dir)

        assert raw_dir.exists()

    def test_fetch_projects_http_url_raises_value_error(self, tmp_path: Path) -> None:
        """fetch_projects should raise ValueError for non-HTTPS URLs."""
        with pytest.raises(ValueError, match="must start with 'https://'"):
            fetch_projects("http://redmine.example.com", "key", tmp_path / "raw")

    def test_fetch_projects_output_is_valid_json_array(self, tmp_path: Path) -> None:
        """Output file should be a JSON array even when project list is empty."""
        with patch("staticmine.fetcher.projects.Redmine") as mock_redmine_cls:
            mock_redmine = MagicMock()
            mock_redmine_cls.return_value = mock_redmine
            mock_redmine.project.all.return_value = []

            raw_dir = tmp_path / "raw"
            fetch_projects("https://redmine.example.com", "test-key", raw_dir)

        with (raw_dir / "projects.json").open(encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 0
