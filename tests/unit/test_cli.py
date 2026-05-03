"""Unit tests for staticmine.cli."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from staticmine.cli import main

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _write_config(tmp_path: Path, url: str = "https://redmine.example.com") -> Path:
    """Write a minimal config YAML and return its path."""
    cfg = tmp_path / "staticmine.yaml"
    cfg.write_text(
        f"redmine:\n  url: {url}\n  api_key: testkey\n",
        encoding="utf-8",
    )
    return cfg


class TestFetchCommand:
    """Tests for 'staticmine fetch' CLI command."""

    def test_fetch_calls_fetch_projects_with_correct_args(self, tmp_path: Path) -> None:
        """fetch command should invoke fetch_projects with URL, key, and output dir."""
        cfg = _write_config(tmp_path)
        runner = CliRunner()

        with patch("staticmine.cli.fetch_projects") as mock_fetch:
            result = runner.invoke(
                main,
                ["fetch", "--config", str(cfg), "--out", str(tmp_path / "raw")],
            )

        assert result.exit_code == 0, result.output
        mock_fetch.assert_called_once_with(
            "https://redmine.example.com",
            "testkey",
            tmp_path / "raw",
        )

    def test_fetch_uses_config_raw_dir_when_no_out(self, tmp_path: Path) -> None:
        """fetch command should use config output.raw when --out is not provided."""
        cfg = tmp_path / "staticmine.yaml"
        cfg.write_text(
            "redmine:\n  url: https://redmine.example.com\n  api_key: key\n"
            "output:\n  raw: /custom/raw/\n",
            encoding="utf-8",
        )
        runner = CliRunner()

        with patch("staticmine.cli.fetch_projects") as mock_fetch:
            result = runner.invoke(main, ["fetch", "--config", str(cfg)])

        assert result.exit_code == 0
        call_args = mock_fetch.call_args[0]
        assert str(call_args[2]).rstrip("/") == "/custom/raw"

    def test_fetch_exits_on_http_url(self, tmp_path: Path) -> None:
        """fetch command should fail when config has an HTTP URL."""
        cfg = _write_config(tmp_path, url="http://redmine.example.com")
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--config", str(cfg)])
        assert result.exit_code != 0


class TestConvertCommand:
    """Tests for 'staticmine convert' CLI command."""

    def test_convert_calls_convert_projects(self, tmp_path: Path) -> None:
        """convert command should invoke convert_projects with raw and content dirs."""
        cfg = _write_config(tmp_path)
        runner = CliRunner()

        with patch("staticmine.cli.convert_projects") as mock_convert:
            result = runner.invoke(
                main,
                [
                    "convert",
                    "--config",
                    str(cfg),
                    "--in",
                    str(tmp_path / "raw"),
                    "--out",
                    str(tmp_path / "content"),
                ],
            )

        assert result.exit_code == 0, result.output
        mock_convert.assert_called_once_with(
            tmp_path / "raw",
            tmp_path / "content",
        )

    def test_convert_uses_config_dirs_when_no_override(self, tmp_path: Path) -> None:
        """convert command should use config dirs when --in/--out not specified."""
        cfg = tmp_path / "staticmine.yaml"
        cfg.write_text(
            "redmine:\n  url: https://redmine.example.com\n  api_key: key\n"
            "output:\n  raw: /in/raw/\n  content: /out/content/\n",
            encoding="utf-8",
        )
        runner = CliRunner()

        with patch("staticmine.cli.convert_projects") as mock_convert:
            result = runner.invoke(main, ["convert", "--config", str(cfg)])

        assert result.exit_code == 0
        args = mock_convert.call_args[0]
        assert str(args[0]).rstrip("/") == "/in/raw"
        assert str(args[1]).rstrip("/") == "/out/content"

    def test_convert_skips_config_when_in_and_out_both_specified(self, tmp_path: Path) -> None:
        """convert command should not load config when both --in and --out are given."""
        runner = CliRunner()

        with patch("staticmine.cli.convert_projects") as mock_convert:
            result = runner.invoke(
                main,
                [
                    "convert",
                    "--in",
                    str(tmp_path / "raw"),
                    "--out",
                    str(tmp_path / "content"),
                ],
            )

        assert result.exit_code == 0, result.output
        mock_convert.assert_called_once_with(
            tmp_path / "raw",
            tmp_path / "content",
        )

    def test_convert_succeeds_without_config_file_when_in_and_out_specified(
        self, tmp_path: Path
    ) -> None:
        """convert should succeed even if staticmine.yaml is absent when --in/--out are given."""
        non_existent_config = str(tmp_path / "staticmine.yaml")
        runner = CliRunner()

        with patch("staticmine.cli.convert_projects"):
            result = runner.invoke(
                main,
                [
                    "convert",
                    "--config",
                    non_existent_config,
                    "--in",
                    str(tmp_path / "raw"),
                    "--out",
                    str(tmp_path / "content"),
                ],
            )

        assert result.exit_code == 0, result.output


class TestBuildCommand:
    """Tests for 'staticmine build' CLI command."""

    def test_build_runs_hugo_subprocess(self, tmp_path: Path) -> None:
        """build command should invoke subprocess.run with hugo arguments."""
        cfg = _write_config(tmp_path)
        runner = CliRunner()

        with patch("staticmine.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(
                main,
                [
                    "build",
                    "--config",
                    str(cfg),
                    "--in",
                    str(tmp_path / "content"),
                    "--out",
                    str(tmp_path / "public"),
                ],
            )

        assert result.exit_code == 0, result.output
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "hugo"
        assert "--contentDir" in cmd
        assert "--destination" in cmd

    def test_build_exits_when_hugo_not_found(self, tmp_path: Path) -> None:
        """build command should exit with error when hugo binary is not found."""
        cfg = _write_config(tmp_path)
        runner = CliRunner()

        with patch("staticmine.cli.subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(main, ["build", "--config", str(cfg)])

        assert result.exit_code != 0

    def test_build_skips_config_when_in_and_out_both_specified(self, tmp_path: Path) -> None:
        """build command should not load config when both --in and --out are given."""
        runner = CliRunner()

        with patch("staticmine.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(
                main,
                [
                    "build",
                    "--in",
                    str(tmp_path / "content"),
                    "--out",
                    str(tmp_path / "public"),
                ],
            )

        assert result.exit_code == 0, result.output
        assert mock_run.called

    def test_build_succeeds_without_config_file_when_in_and_out_specified(
        self, tmp_path: Path
    ) -> None:
        """build should succeed even if staticmine.yaml is absent when --in/--out are both given."""
        non_existent_config = str(tmp_path / "staticmine.yaml")
        runner = CliRunner()

        with patch("staticmine.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(
                main,
                [
                    "build",
                    "--config",
                    non_existent_config,
                    "--in",
                    str(tmp_path / "content"),
                    "--out",
                    str(tmp_path / "public"),
                ],
            )

        assert result.exit_code == 0, result.output
