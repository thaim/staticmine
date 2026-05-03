"""Smoke integration tests: Converter → Hugo build."""

import shutil
import subprocess
from pathlib import Path

import pytest

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
