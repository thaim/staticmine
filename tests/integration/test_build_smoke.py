"""Smoke integration tests: Converter → Hugo build."""

import shutil
import subprocess
from pathlib import Path

import pytest

from staticmine.converter.issues import convert_issues
from staticmine.converter.projects import convert_projects

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _hugo_available() -> bool:
    """Check whether the 'hugo' binary is available in PATH."""
    return shutil.which("hugo") is not None


@pytest.mark.skipif(not _hugo_available(), reason="hugo binary not found in PATH")
class TestBuildSmoke:
    """End-to-end smoke tests: fixtures → convert → hugo build."""

    def test_converter_generates_index_md_from_fixture(self, tmp_path: Path) -> None:
        """Converter should produce _index.md files from the fixture projects.json."""
        content_dir = tmp_path / "content"
        convert_projects(FIXTURES_DIR / "raw", content_dir)

        for identifier in ("alpha", "beta", "gamma"):
            index_md = content_dir / "projects" / identifier / "_index.md"
            assert index_md.exists(), f"Expected {index_md} to exist"

    def test_hugo_build_produces_project_list_html(self, tmp_path: Path) -> None:
        """Hugo build should produce public/projects/index.html."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Hugo build failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        projects_index = public_dir / "projects" / "index.html"
        assert projects_index.exists(), f"Expected {projects_index} to exist after Hugo build"

    def test_hugo_build_project_list_contains_project_links(self, tmp_path: Path) -> None:
        """The generated projects/index.html should contain project links."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        html = (public_dir / "projects" / "index.html").read_text(encoding="utf-8")
        assert "alpha" in html
        assert "beta" in html
        assert "gamma" in html

    def test_convert_issues_generates_page_bundle_from_fixture(self, tmp_path: Path) -> None:
        """convert_issues should produce Page Bundle files from the fixture issues.json."""
        content_dir = tmp_path / "content"
        convert_projects(FIXTURES_DIR / "raw", content_dir)
        convert_issues(FIXTURES_DIR / "raw", content_dir)

        # alpha project has 2 issues
        assert (content_dir / "projects" / "alpha" / "issues" / "_index.md").exists()
        assert (content_dir / "projects" / "alpha" / "issues" / "1" / "index.md").exists()
        assert (content_dir / "projects" / "alpha" / "issues" / "2" / "index.md").exists()

        # Verify frontmatter keys exist
        index_md = content_dir / "projects" / "alpha" / "issues" / "1" / "index.md"
        text = index_md.read_text(encoding="utf-8")
        required_keys = (
            "id:",
            "title:",
            "status:",
            "tracker:",
            "priority:",
            "created_on:",
            "updated_on:",
            "project_identifier:",
            "project_is_public:",
        )
        for key in required_keys:
            assert key in text, f"Expected key '{key}' in frontmatter"

    def test_hugo_build_produces_issues_list_html(self, tmp_path: Path) -> None:
        """Hugo build should produce public/projects/alpha/issues/index.html."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)
        convert_issues(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Hugo build failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        issues_index = public_dir / "projects" / "alpha" / "issues" / "index.html"
        assert issues_index.exists(), f"Expected {issues_index} to exist after Hugo build"

    def test_hugo_build_produces_issue_single_html(self, tmp_path: Path) -> None:
        """Hugo build should produce public/projects/alpha/issues/1/index.html."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)
        convert_issues(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Hugo build failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        issue_single = public_dir / "projects" / "alpha" / "issues" / "1" / "index.html"
        assert issue_single.exists(), f"Expected {issue_single} to exist after Hugo build"

    def test_hugo_build_issues_list_contains_issue_data(self, tmp_path: Path) -> None:
        """The generated issues/index.html should contain issue IDs, titles, and statuses."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)
        convert_issues(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        issues_index_html = public_dir / "projects" / "alpha" / "issues" / "index.html"
        html = issues_index_html.read_text(encoding="utf-8")
        assert "サンプルチケット1" in html
        assert "New" in html

    def test_hugo_build_project_single_has_issues_link(self, tmp_path: Path) -> None:
        """Project detail page should contain a link to the issues list."""
        content_dir = tmp_path / "content"
        public_dir = tmp_path / "public"

        convert_projects(FIXTURES_DIR / "raw", content_dir)
        convert_issues(FIXTURES_DIR / "raw", content_dir)

        cmd = [
            "hugo",
            "--source",
            str(PROJECT_ROOT / "hugo"),
            "--contentDir",
            str(content_dir.resolve()),
            "--destination",
            str(public_dir.resolve()),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        html = (public_dir / "projects" / "alpha" / "index.html").read_text(encoding="utf-8")
        assert "issues/" in html or "Issue 一覧" in html
