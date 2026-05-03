"""Unit tests for staticmine.converter.projects."""

import hashlib
import json
from pathlib import Path

import pytest

from staticmine.converter.projects import _build_frontmatter, convert_projects

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestBuildFrontmatter:
    """Unit tests for _build_frontmatter helper."""

    def test_build_frontmatter_contains_required_fields(self) -> None:
        """frontmatter must contain identifier, name, project_is_public, created_on."""
        project = {
            "identifier": "myproject",
            "name": "My Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project)
        assert 'identifier: "myproject"' in result
        assert 'name: "My Project"' in result
        assert "project_is_public: true" in result
        assert 'created_on: "2021-01-01T00:00:00Z"' in result

    def test_build_frontmatter_false_public_flag(self) -> None:
        """project_is_public should be 'false' for private projects."""
        project = {
            "identifier": "private",
            "name": "Private Project",
            "is_public": False,
            "created_on": "2022-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project)
        assert "project_is_public: false" in result

    def test_build_frontmatter_field_order_is_fixed(self) -> None:
        """Fields must appear in the fixed order for idempotency."""
        project = {
            "identifier": "ordered",
            "name": "Ordered Project",
            "is_public": True,
            "created_on": "2020-06-15T10:00:00Z",
        }
        result = _build_frontmatter(project)
        lines = result.splitlines()
        assert lines[0] == "---"
        assert lines[1].startswith("identifier:")
        assert lines[2].startswith("name:")
        assert lines[3].startswith("project_is_public:")
        assert lines[4].startswith("created_on:")
        assert lines[5] == "---"

    def test_build_frontmatter_delimiters_present(self) -> None:
        """Frontmatter must be wrapped in --- delimiters."""
        project = {
            "identifier": "x",
            "name": "X",
            "is_public": False,
            "created_on": "2023-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project)
        assert result.startswith("---\n")
        assert "\n---\n" in result


class TestConvertProjects:
    """Integration-style tests for convert_projects."""

    def _write_projects_json(self, raw_dir: Path, projects: list[dict]) -> None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "projects.json").write_text(
            json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def test_convert_projects_generates_index_md_files(self, tmp_path: Path) -> None:
        """Each project should produce content/projects/<identifier>/_index.md."""
        projects = [
            {
                "id": 1,
                "identifier": "alpha",
                "name": "Alpha",
                "is_public": True,
                "created_on": "2021-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "identifier": "beta",
                "name": "Beta",
                "is_public": False,
                "created_on": "2022-01-01T00:00:00Z",
            },
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)

        assert (content_dir / "projects" / "alpha" / "_index.md").exists()
        assert (content_dir / "projects" / "beta" / "_index.md").exists()

    def test_convert_projects_frontmatter_content_correct(self, tmp_path: Path) -> None:
        """Generated _index.md should have correct frontmatter values."""
        projects = [
            {
                "id": 1,
                "identifier": "myproject",
                "name": "My Project",
                "is_public": True,
                "created_on": "2021-06-15T12:00:00Z",
            }
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)

        index_md = content_dir / "projects" / "myproject" / "_index.md"
        text = index_md.read_text(encoding="utf-8")
        assert 'identifier: "myproject"' in text
        assert 'name: "My Project"' in text
        assert "project_is_public: true" in text
        assert 'created_on: "2021-06-15T12:00:00Z"' in text

    def test_convert_projects_idempotent_sha256_unchanged(self, tmp_path: Path) -> None:
        """Running convert twice should produce identical files (SHA-256 match)."""
        projects = [
            {
                "id": 1,
                "identifier": "stable",
                "name": "Stable Project",
                "is_public": True,
                "created_on": "2021-01-01T00:00:00Z",
            }
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)
        index_path = content_dir / "projects" / "stable" / "_index.md"
        hash_first = _sha256(index_path)

        convert_projects(raw_dir, content_dir)
        hash_second = _sha256(index_path)

        assert hash_first == hash_second, "SHA-256 must not change on second run"

    def test_convert_projects_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        """convert_projects should create the output directory tree if absent."""
        projects = [
            {
                "id": 1,
                "identifier": "newdir",
                "name": "New Dir",
                "is_public": False,
                "created_on": "2021-01-01T00:00:00Z",
            },
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "deep" / "nested" / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)

        assert (content_dir / "projects" / "newdir" / "_index.md").exists()

    def test_convert_projects_fixture_file(self) -> None:
        """Convert should work with the shared fixture projects.json."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            content_dir = Path(tmp) / "content"
            convert_projects(FIXTURES_DIR / "raw", content_dir)

            assert (content_dir / "projects" / "alpha" / "_index.md").exists()
            assert (content_dir / "projects" / "beta" / "_index.md").exists()
            assert (content_dir / "projects" / "gamma" / "_index.md").exists()

    def test_convert_projects_missing_raw_raises(self, tmp_path: Path) -> None:
        """Missing raw/projects.json should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="raw projects file not found"):
            convert_projects(tmp_path / "nonexistent", tmp_path / "content")
