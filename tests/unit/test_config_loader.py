"""Unit tests for staticmine.config.loader."""

import textwrap
from pathlib import Path

import pytest

from staticmine.config.loader import (
    DEFAULT_CONTENT_DIR,
    DEFAULT_PUBLIC_DIR,
    DEFAULT_RAW_DIR,
    load_config,
)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    """Write a YAML string to a temp file and return its path."""
    p = tmp_path / "staticmine.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestLoadConfigSuccess:
    """Tests for successful configuration loading."""

    def test_load_config_minimal_returns_correct_values(self, tmp_path: Path) -> None:
        """Minimal config (no output section) uses default dirs."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              url: https://redmine.example.com
              api_key: secret123
            """,
        )
        cfg = load_config(cfg_path)
        assert cfg.redmine_url == "https://redmine.example.com"
        assert cfg.api_key == "secret123"
        assert cfg.raw_dir == DEFAULT_RAW_DIR
        assert cfg.content_dir == DEFAULT_CONTENT_DIR
        assert cfg.public_dir == DEFAULT_PUBLIC_DIR

    def test_load_config_with_output_section_overrides_defaults(self, tmp_path: Path) -> None:
        """Explicit output section values override defaults."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              url: https://redmine.example.com
              api_key: mykey
            output:
              raw: /data/raw/
              content: /data/content/
              public: /data/public/
            """,
        )
        cfg = load_config(cfg_path)
        assert cfg.raw_dir == "/data/raw/"
        assert cfg.content_dir == "/data/content/"
        assert cfg.public_dir == "/data/public/"


class TestLoadConfigErrors:
    """Tests for configuration validation errors."""

    def test_load_config_http_url_raises_value_error(self, tmp_path: Path) -> None:
        """HTTP URL (not HTTPS) should raise ValueError."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              url: http://redmine.example.com
              api_key: secret
            """,
        )
        with pytest.raises(ValueError, match="must start with 'https://'"):
            load_config(cfg_path)

    def test_load_config_missing_redmine_section_raises_value_error(self, tmp_path: Path) -> None:
        """Missing 'redmine' section should raise ValueError."""
        cfg_path = _write_yaml(tmp_path, "output:\n  raw: raw/\n")
        with pytest.raises(ValueError, match="Missing required section: 'redmine'"):
            load_config(cfg_path)

    def test_load_config_missing_url_raises_value_error(self, tmp_path: Path) -> None:
        """Missing 'redmine.url' should raise ValueError."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              api_key: secret
            """,
        )
        with pytest.raises(ValueError, match=r"Missing required field: 'redmine\.url'"):
            load_config(cfg_path)

    def test_load_config_missing_api_key_raises_value_error(self, tmp_path: Path) -> None:
        """Missing 'redmine.api_key' should raise ValueError."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              url: https://redmine.example.com
            """,
        )
        with pytest.raises(ValueError, match=r"Missing required field: 'redmine\.api_key'"):
            load_config(cfg_path)

    def test_load_config_file_not_found_raises(self, tmp_path: Path) -> None:
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_load_config_plain_string_url_without_scheme_raises(self, tmp_path: Path) -> None:
        """URL without scheme should raise ValueError."""
        cfg_path = _write_yaml(
            tmp_path,
            """
            redmine:
              url: redmine.example.com
              api_key: secret
            """,
        )
        with pytest.raises(ValueError, match="must start with 'https://'"):
            load_config(cfg_path)
