"""Unit tests for staticmine.converter.issues."""

import hashlib
import json
from pathlib import Path

import pytest

from staticmine.converter.issues import _build_frontmatter, _build_section_index, convert_issues

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_projects_json(raw_dir: Path, projects: list[dict]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "projects.json").write_text(
        json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _write_issues_json(raw_dir: Path, identifier: str, issues: list[dict]) -> None:
    issues_dir = raw_dir / "projects" / identifier
    issues_dir.mkdir(parents=True, exist_ok=True)
    payload = {"total_count": len(issues), "issues": issues}
    (issues_dir / "issues.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _make_issue(
    issue_id: int,
    identifier: str,
    subject: str = "Test Issue",
    status_name: str = "New",
    tracker_name: str = "Bug",
    priority_name: str = "Normal",
    created_on: str = "2021-01-15T10:00:00Z",
    updated_on: str = "2021-02-01T09:30:00Z",
) -> dict:
    project_name = f"{identifier.capitalize()} Project"
    return {
        "id": issue_id,
        "project": {"id": 1, "identifier": identifier, "name": project_name},
        "subject": subject,
        "status": {"id": 1, "name": status_name},
        "tracker": {"id": 1, "name": tracker_name},
        "priority": {"id": 2, "name": priority_name},
        "created_on": created_on,
        "updated_on": updated_on,
    }


class TestBuildFrontmatter:
    """Unit tests for _build_frontmatter helper."""

    def test_build_frontmatter_contains_required_fields(self) -> None:
        """frontmatter must contain all required fields."""
        issue = _make_issue(1, "alpha", subject="サンプルチケット", status_name="New")
        result = _build_frontmatter(issue, project_is_public=True)
        assert "id: 1" in result
        assert 'title: "サンプルチケット"' in result
        assert 'status: "New"' in result
        assert 'tracker: "Bug"' in result
        assert 'priority: "Normal"' in result
        assert 'created_on: "2021-01-15T10:00:00Z"' in result
        assert 'updated_on: "2021-02-01T09:30:00Z"' in result
        assert 'project_identifier: "alpha"' in result
        assert "project_is_public: true" in result

    def test_build_frontmatter_false_public_flag(self) -> None:
        """project_is_public should be 'false' for private projects."""
        issue = _make_issue(1, "beta")
        result = _build_frontmatter(issue, project_is_public=False)
        assert "project_is_public: false" in result

    def test_build_frontmatter_field_order_is_fixed(self) -> None:
        """Fields must appear in a fixed order for idempotency."""
        issue = _make_issue(42, "alpha")
        result = _build_frontmatter(issue, project_is_public=True)
        lines = result.splitlines()
        assert lines[0] == "---"
        assert lines[1].startswith("id:")
        assert lines[2].startswith("title:")
        assert lines[3].startswith("status:")
        assert lines[4].startswith("tracker:")
        assert lines[5].startswith("priority:")
        assert lines[6].startswith("created_on:")
        assert lines[7].startswith("updated_on:")
        assert lines[8].startswith("project_identifier:")
        assert lines[9].startswith("project_is_public:")
        assert lines[10].startswith("type:")
        assert lines[11] == "---"

    def test_build_frontmatter_contains_placeholder_body(self) -> None:
        """Page content must contain the M3 placeholder text."""
        issue = _make_issue(1, "alpha")
        result = _build_frontmatter(issue, project_is_public=True)
        assert "詳細は準備中です。" in result

    def test_build_frontmatter_delimiters_present(self) -> None:
        """Frontmatter must be wrapped in --- delimiters."""
        issue = _make_issue(1, "alpha")
        result = _build_frontmatter(issue, project_is_public=True)
        assert result.startswith("---\n")
        assert "\n---\n" in result


class TestBuildSectionIndex:
    """Unit tests for _build_section_index helper."""

    def test_section_index_has_title_issues(self) -> None:
        """_index.md must contain title: Issues."""
        result = _build_section_index()
        assert 'title: "Issues"' in result

    def test_section_index_has_type_issues(self) -> None:
        """_index.md must contain type: issues for Hugo template selection."""
        result = _build_section_index()
        assert 'type: "issues"' in result

    def test_section_index_has_frontmatter_delimiters(self) -> None:
        """_index.md must be wrapped in --- delimiters."""
        result = _build_section_index()
        assert result.startswith("---\n")
        assert "\n---\n" in result


class TestConvertIssues:
    """Integration-style tests for convert_issues."""

    def test_convert_issues_generates_page_bundle(self, tmp_path: Path) -> None:
        """Each issue should produce content/projects/<id>/issues/<id>/index.md."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 1, "identifier": "alpha", "name": "Alpha", "is_public": True}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "alpha", [_make_issue(1, "alpha"), _make_issue(2, "alpha")])

        convert_issues(raw_dir, content_dir)

        assert (content_dir / "projects" / "alpha" / "issues" / "1" / "index.md").exists()
        assert (content_dir / "projects" / "alpha" / "issues" / "2" / "index.md").exists()

    def test_convert_issues_generates_section_index(self, tmp_path: Path) -> None:
        """convert_issues should generate issues/_index.md for each project."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 1, "identifier": "alpha", "name": "Alpha", "is_public": True}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "alpha", [_make_issue(1, "alpha")])

        convert_issues(raw_dir, content_dir)

        section_index = content_dir / "projects" / "alpha" / "issues" / "_index.md"
        assert section_index.exists()
        text = section_index.read_text(encoding="utf-8")
        assert 'title: "Issues"' in text

    def test_convert_issues_frontmatter_content_correct(self, tmp_path: Path) -> None:
        """Generated index.md should have correct frontmatter values."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 1, "identifier": "alpha", "name": "Alpha", "is_public": True}]
        _write_projects_json(raw_dir, projects)
        issue = _make_issue(
            1,
            "alpha",
            subject="テストチケット",
            status_name="In Progress",
            tracker_name="Feature",
            priority_name="High",
            created_on="2021-03-01T00:00:00Z",
            updated_on="2021-04-01T00:00:00Z",
        )
        _write_issues_json(raw_dir, "alpha", [issue])

        convert_issues(raw_dir, content_dir)

        index_md = content_dir / "projects" / "alpha" / "issues" / "1" / "index.md"
        text = index_md.read_text(encoding="utf-8")
        assert "id: 1" in text
        assert 'title: "テストチケット"' in text
        assert 'status: "In Progress"' in text
        assert 'tracker: "Feature"' in text
        assert 'priority: "High"' in text
        assert 'created_on: "2021-03-01T00:00:00Z"' in text
        assert 'updated_on: "2021-04-01T00:00:00Z"' in text
        assert 'project_identifier: "alpha"' in text
        assert "project_is_public: true" in text

    def test_convert_issues_project_is_public_from_projects_json(self, tmp_path: Path) -> None:
        """project_is_public should be read from projects.json, not from issues.json."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 2, "identifier": "beta", "name": "Beta", "is_public": False}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "beta", [_make_issue(3, "beta")])

        convert_issues(raw_dir, content_dir)

        index_md = content_dir / "projects" / "beta" / "issues" / "3" / "index.md"
        text = index_md.read_text(encoding="utf-8")
        assert "project_is_public: false" in text

    def test_convert_issues_idempotent_sha256_unchanged(self, tmp_path: Path) -> None:
        """Running convert_issues twice should produce identical files (SHA-256 match)."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 1, "identifier": "stable", "name": "Stable", "is_public": True}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "stable", [_make_issue(10, "stable")])

        convert_issues(raw_dir, content_dir)
        index_path = content_dir / "projects" / "stable" / "issues" / "10" / "index.md"
        hash_first = _sha256(index_path)

        convert_issues(raw_dir, content_dir)
        hash_second = _sha256(index_path)

        assert hash_first == hash_second, "SHA-256 must not change on second run"

    def test_convert_issues_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        """convert_issues should create the output directory tree if absent."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "deep" / "nested" / "content"
        projects = [{"id": 1, "identifier": "newdir", "name": "NewDir", "is_public": False}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "newdir", [_make_issue(5, "newdir")])

        convert_issues(raw_dir, content_dir)

        assert (content_dir / "projects" / "newdir" / "issues" / "5" / "index.md").exists()

    def test_convert_issues_missing_raw_raises(self, tmp_path: Path) -> None:
        """Missing raw/projects.json should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="raw projects file not found"):
            convert_issues(tmp_path / "nonexistent", tmp_path / "content")

    def test_convert_issues_fixture_files(self) -> None:
        """convert_issues should work with the shared fixture files."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            content_dir = Path(tmp) / "content"
            convert_issues(FIXTURES_DIR / "raw", content_dir)

            assert (content_dir / "projects" / "alpha" / "issues" / "_index.md").exists()
            assert (content_dir / "projects" / "alpha" / "issues" / "1" / "index.md").exists()
            assert (content_dir / "projects" / "alpha" / "issues" / "2" / "index.md").exists()
            assert (content_dir / "projects" / "beta" / "issues" / "_index.md").exists()
            assert (content_dir / "projects" / "beta" / "issues" / "3" / "index.md").exists()

    def test_convert_issues_empty_issue_list_generates_section_only(self, tmp_path: Path) -> None:
        """For projects with no issues, only _index.md should be created."""
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        projects = [{"id": 1, "identifier": "empty", "name": "Empty", "is_public": True}]
        _write_projects_json(raw_dir, projects)
        _write_issues_json(raw_dir, "empty", [])

        convert_issues(raw_dir, content_dir)

        section_index = content_dir / "projects" / "empty" / "issues" / "_index.md"
        assert section_index.exists()
        # No individual issue directories should be created
        issues_dir = content_dir / "projects" / "empty" / "issues"
        subdirs = [p for p in issues_dir.iterdir() if p.is_dir()]
        assert len(subdirs) == 0
