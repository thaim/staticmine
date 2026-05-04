"""Unit tests for staticmine.fetcher.issues."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from staticmine.fetcher.issues import fetch_issues

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_response(
    issues: list[dict],
    total_count: int,
    offset: int = 0,
    limit: int = 100,
    status_code: int = 200,
) -> MagicMock:
    """Create a mock requests.Response for the issues endpoint."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "issues": issues,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
    }
    return mock_resp


def _make_issue(
    issue_id: int,
    identifier: str,
    subject: str = "Test Issue",
    status_name: str = "New",
    tracker_name: str = "Bug",
    priority_name: str = "Normal",
) -> dict:
    """Create a minimal issue dict as returned by Redmine API."""
    project_name = f"{identifier.capitalize()} Project"
    return {
        "id": issue_id,
        "project": {"id": 1, "identifier": identifier, "name": project_name},
        "subject": subject,
        "status": {"id": 1, "name": status_name},
        "tracker": {"id": 1, "name": tracker_name},
        "priority": {"id": 2, "name": priority_name},
        "created_on": "2021-01-01T00:00:00Z",
        "updated_on": "2021-06-01T00:00:00Z",
    }


def _write_projects_json(raw_dir: Path, projects: list[dict]) -> None:
    """Write a projects.json fixture to raw_dir."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "projects.json").write_text(
        json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class TestFetchIssues:
    """Tests for fetch_issues function."""

    def test_fetch_issues_creates_output_file(self, tmp_path: Path) -> None:
        """fetch_issues should create raw/projects/<identifier>/issues.json."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "alpha", "name": "Alpha"}])

        issue = _make_issue(1, "alpha")
        mock_resp = _make_response([issue], total_count=1)

        with patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects" / "alpha" / "issues.json"
        assert output_path.exists(), "issues.json should be created"

    def test_fetch_issues_output_has_correct_structure(self, tmp_path: Path) -> None:
        """Output issues.json should have total_count and issues keys."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "alpha", "name": "Alpha"}])

        issues = [_make_issue(1, "alpha"), _make_issue(2, "alpha")]
        mock_resp = _make_response(issues, total_count=2)

        with patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects" / "alpha" / "issues.json"
        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert "total_count" in data
        assert "issues" in data
        assert data["total_count"] == 2
        assert len(data["issues"]) == 2

    def test_fetch_issues_pagination_fetches_all_pages(self, tmp_path: Path) -> None:
        """fetch_issues should follow pagination until all issues are retrieved."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "alpha", "name": "Alpha"}])

        page1_issues = [_make_issue(i, "alpha") for i in range(1, 101)]
        page2_issues = [_make_issue(i, "alpha") for i in range(101, 151)]

        page1_resp = _make_response(page1_issues, total_count=150, offset=0)
        page2_resp = _make_response(page2_issues, total_count=150, offset=100)

        with patch(
            "staticmine.fetcher.issues.requests.get",
            side_effect=[page1_resp, page2_resp],
        ):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects" / "alpha" / "issues.json"
        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_count"] == 150
        assert len(data["issues"]) == 150

    def test_fetch_issues_empty_project_returns_empty_list(self, tmp_path: Path) -> None:
        """fetch_issues should write issues.json with empty list for projects with no issues."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 2, "identifier": "beta", "name": "Beta"}])

        mock_resp = _make_response([], total_count=0)

        with patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        output_path = raw_dir / "projects" / "beta" / "issues.json"
        assert output_path.exists()

        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_count"] == 0
        assert data["issues"] == []

    def test_fetch_issues_creates_project_dir_if_missing(self, tmp_path: Path) -> None:
        """fetch_issues should create raw/projects/<identifier>/ if it does not exist."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "newproject", "name": "New"}])

        mock_resp = _make_response([], total_count=0)

        project_dir = raw_dir / "projects" / "newproject"
        assert not project_dir.exists()

        with patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        assert project_dir.exists()

    def test_fetch_issues_http_url_raises_value_error(self, tmp_path: Path) -> None:
        """fetch_issues should raise ValueError for non-HTTPS URLs."""
        with pytest.raises(ValueError, match="must start with 'https://'"):
            fetch_issues("http://redmine.example.com", "key", tmp_path / "raw")

    def test_fetch_issues_missing_projects_json_raises(self, tmp_path: Path) -> None:
        """fetch_issues should raise FileNotFoundError if projects.json is missing."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(FileNotFoundError, match="raw projects file not found"):
            fetch_issues("https://redmine.example.com", "key", raw_dir)

    def test_fetch_issues_multiple_projects(self, tmp_path: Path) -> None:
        """fetch_issues should process each project in projects.json."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(
            raw_dir,
            [
                {"id": 1, "identifier": "alpha", "name": "Alpha"},
                {"id": 2, "identifier": "beta", "name": "Beta"},
            ],
        )

        alpha_issue = _make_issue(1, "alpha")
        beta_issue = _make_issue(2, "beta")
        mock_alpha = _make_response([alpha_issue], total_count=1)
        mock_beta = _make_response([beta_issue], total_count=1)

        with patch(
            "staticmine.fetcher.issues.requests.get",
            side_effect=[mock_alpha, mock_beta],
        ):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        assert (raw_dir / "projects" / "alpha" / "issues.json").exists()
        assert (raw_dir / "projects" / "beta" / "issues.json").exists()

    def test_fetch_issues_api_request_includes_required_params(self, tmp_path: Path) -> None:
        """fetch_issues should request status_id=* to retrieve all statuses."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "alpha", "name": "Alpha"}])

        mock_resp = _make_response([], total_count=0)

        with patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp) as mock_get:
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)

        call_args = mock_get.call_args
        if len(call_args.args) > 1:
            params = call_args.kwargs.get("params") or call_args.args[1]
        else:
            params = call_args.kwargs.get("params")
        assert params is not None
        assert params.get("status_id") == "*"
        assert params.get("project_id") == "alpha"
        assert params.get("limit") == 100

    def test_fetch_issues_http_error_propagates(self, tmp_path: Path) -> None:
        """fetch_issues should propagate HTTP errors from the API."""
        raw_dir = tmp_path / "raw"
        _write_projects_json(raw_dir, [{"id": 1, "identifier": "alpha", "name": "Alpha"}])

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")

        with (
            patch("staticmine.fetcher.issues.requests.get", return_value=mock_resp),
            pytest.raises(requests.HTTPError),
        ):
            fetch_issues("https://redmine.example.com", "test-key", raw_dir)
