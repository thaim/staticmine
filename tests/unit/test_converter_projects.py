"""Unit tests for staticmine.converter.projects."""

import hashlib
import json
import logging
from pathlib import Path

import pytest

from staticmine.converter.projects import _build_frontmatter, convert_projects

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_id_to_project(projects: list[dict]) -> dict:
    return {p["id"]: p for p in projects if "id" in p}


class TestBuildFrontmatter:
    """Unit tests for _build_frontmatter helper."""

    def test_build_frontmatter_contains_required_fields(self) -> None:
        """frontmatter must contain id, identifier, name, project_is_public, created_on."""
        project = {
            "id": 1,
            "identifier": "myproject",
            "name": "My Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project, {})
        assert "id: 1" in result
        assert 'identifier: "myproject"' in result
        assert 'name: "My Project"' in result
        assert "project_is_public: true" in result
        assert 'created_on: "2021-01-01T00:00:00Z"' in result

    def test_build_frontmatter_false_public_flag(self) -> None:
        """project_is_public should be 'false' for private projects."""
        project = {
            "id": 2,
            "identifier": "private",
            "name": "Private Project",
            "is_public": False,
            "created_on": "2022-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project, {})
        assert "project_is_public: false" in result

    def test_build_frontmatter_field_order_is_fixed(self) -> None:
        """Fields must appear in the fixed order for idempotency."""
        project = {
            "id": 5,
            "identifier": "ordered",
            "name": "Ordered Project",
            "is_public": True,
            "created_on": "2020-06-15T10:00:00Z",
        }
        result = _build_frontmatter(project, {})
        lines = result.splitlines()
        assert lines[0] == "---"
        assert lines[1].startswith("id:")
        assert lines[2].startswith("identifier:")
        assert lines[3].startswith("name:")
        assert lines[4].startswith("project_is_public:")
        assert lines[5].startswith("created_on:")
        assert lines[6] == "---"

    def test_build_frontmatter_field_order_with_parent(self) -> None:
        """parent_identifier and parent_name must appear after created_on."""
        parent = {
            "id": 1,
            "identifier": "alpha",
            "name": "Alpha Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        project = {
            "id": 3,
            "identifier": "gamma",
            "name": "Gamma Sub",
            "is_public": True,
            "created_on": "2023-05-10T08:30:00Z",
            "parent_id": 1,
        }
        id_to_project = {1: parent}
        result = _build_frontmatter(project, id_to_project)
        lines = result.splitlines()
        assert lines[0] == "---"
        assert lines[1].startswith("id:")
        assert lines[2].startswith("identifier:")
        assert lines[3].startswith("name:")
        assert lines[4].startswith("project_is_public:")
        assert lines[5].startswith("created_on:")
        assert lines[6].startswith("parent_identifier:")
        assert lines[7].startswith("parent_name:")
        assert lines[8] == "---"

    def test_build_frontmatter_delimiters_present(self) -> None:
        """Frontmatter must be wrapped in --- delimiters."""
        project = {
            "id": 9,
            "identifier": "x",
            "name": "X",
            "is_public": False,
            "created_on": "2023-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project, {})
        assert result.startswith("---\n")
        assert "\n---\n" in result

    def test_build_frontmatter_id_is_output(self) -> None:
        """id field must be output in frontmatter."""
        project = {
            "id": 42,
            "identifier": "answer",
            "name": "Answer Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project, {})
        assert "id: 42" in result

    def test_build_frontmatter_parent_fields_output_when_parent_exists(self) -> None:
        """parent_identifier and parent_name must be output when parent_id resolves."""
        parent = {
            "id": 1,
            "identifier": "alpha",
            "name": "Alpha Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        project = {
            "id": 3,
            "identifier": "gamma",
            "name": "Gamma Sub",
            "is_public": True,
            "created_on": "2023-05-10T08:30:00Z",
            "parent_id": 1,
        }
        id_to_project = {1: parent}
        result = _build_frontmatter(project, id_to_project)
        assert 'parent_identifier: "alpha"' in result
        assert 'parent_name: "Alpha Project"' in result

    def test_build_frontmatter_no_parent_fields_when_no_parent(self) -> None:
        """parent_identifier and parent_name must NOT be output for root projects."""
        project = {
            "id": 1,
            "identifier": "alpha",
            "name": "Alpha Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
        }
        result = _build_frontmatter(project, {})
        assert "parent_identifier" not in result
        assert "parent_name" not in result

    def test_build_frontmatter_warns_and_skips_parent_when_unresolvable(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning log is emitted and parent fields are skipped when parent_id is unresolvable."""
        project = {
            "id": 99,
            "identifier": "orphan",
            "name": "Orphan Project",
            "is_public": True,
            "created_on": "2021-01-01T00:00:00Z",
            "parent_id": 999,  # No matching project
        }
        with caplog.at_level(logging.WARNING, logger="staticmine.converter.projects"):
            result = _build_frontmatter(project, {})
        assert "parent_identifier" not in result
        assert "parent_name" not in result
        assert "999" in caplog.text


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
        assert "id: 1" in text
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
            assert (content_dir / "projects" / "delta" / "_index.md").exists()

    def test_convert_projects_missing_raw_raises(self, tmp_path: Path) -> None:
        """Missing raw/projects.json should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="raw projects file not found"):
            convert_projects(tmp_path / "nonexistent", tmp_path / "content")

    def test_convert_projects_description_as_body(self, tmp_path: Path) -> None:
        """description should be output as body text after frontmatter."""
        projects = [
            {
                "id": 1,
                "identifier": "alpha",
                "name": "Alpha Project",
                "description": "The first project",
                "is_public": True,
                "created_on": "2021-01-01T00:00:00Z",
            }
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)

        text = (content_dir / "projects" / "alpha" / "_index.md").read_text(encoding="utf-8")
        # Verify body appears after the closing --- delimiter
        closing_delim_pos = text.index("---\n", 1)
        body_section = text[closing_delim_pos + 4 :]
        assert "The first project" in body_section

    def test_convert_projects_empty_description_no_body(self, tmp_path: Path) -> None:
        """Empty description should produce no body (frontmatter only)."""
        projects = [
            {
                "id": 10,
                "identifier": "nodesc",
                "name": "No Description",
                "description": "",
                "is_public": True,
                "created_on": "2021-01-01T00:00:00Z",
            }
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        convert_projects(raw_dir, content_dir)

        text = (content_dir / "projects" / "nodesc" / "_index.md").read_text(encoding="utf-8")
        # After the closing ---, there should be only an empty line (no body)
        closing_delim_pos = text.index("---\n", 1)
        body_section = text[closing_delim_pos + 4 :]
        assert body_section.strip() == ""

    def test_convert_projects_gamma_has_parent_identifier(self, tmp_path: Path) -> None:
        """gamma project should have parent_identifier: alpha from fixture."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            content_dir = Path(tmp) / "content"
            convert_projects(FIXTURES_DIR / "raw", content_dir)

            text = (content_dir / "projects" / "gamma" / "_index.md").read_text(encoding="utf-8")
            assert 'parent_identifier: "alpha"' in text
            assert 'parent_name: "Alpha Project"' in text

    def test_convert_projects_alpha_has_no_parent_fields(self, tmp_path: Path) -> None:
        """alpha project (root) should NOT have parent_identifier or parent_name."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            content_dir = Path(tmp) / "content"
            convert_projects(FIXTURES_DIR / "raw", content_dir)

            text = (content_dir / "projects" / "alpha" / "_index.md").read_text(encoding="utf-8")
            assert "parent_identifier" not in text
            assert "parent_name" not in text

    def test_convert_projects_unresolvable_parent_id_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unresolvable parent_id should emit warning and skip parent fields."""
        projects = [
            {
                "id": 50,
                "identifier": "orphan",
                "name": "Orphan Project",
                "is_public": True,
                "created_on": "2021-01-01T00:00:00Z",
                "parent_id": 9999,
            }
        ]
        raw_dir = tmp_path / "raw"
        content_dir = tmp_path / "content"
        self._write_projects_json(raw_dir, projects)

        with caplog.at_level(logging.WARNING, logger="staticmine.converter.projects"):
            convert_projects(raw_dir, content_dir)

        text = (content_dir / "projects" / "orphan" / "_index.md").read_text(encoding="utf-8")
        assert "parent_identifier" not in text
        assert "parent_name" not in text
        assert "9999" in caplog.text
