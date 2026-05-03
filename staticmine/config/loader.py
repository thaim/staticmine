"""YAML configuration file loader and validator for staticmine."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_RAW_DIR = "raw/"
DEFAULT_CONTENT_DIR = "content/"
DEFAULT_PUBLIC_DIR = "public/"


class Config:
    """Holds validated staticmine configuration.

    Attributes:
        redmine_url: The Redmine base URL (must start with https://).
        api_key: The Redmine API key.
        raw_dir: Output directory for raw JSON dumps.
        content_dir: Output directory for Markdown content.
        public_dir: Output directory for the built static site.
    """

    def __init__(
        self,
        redmine_url: str,
        api_key: str,
        raw_dir: str = DEFAULT_RAW_DIR,
        content_dir: str = DEFAULT_CONTENT_DIR,
        public_dir: str = DEFAULT_PUBLIC_DIR,
    ) -> None:
        """Initialize Config.

        Args:
            redmine_url: Redmine base URL.
            api_key: Redmine API key.
            raw_dir: Raw JSON output directory.
            content_dir: Markdown content output directory.
            public_dir: Static site output directory.
        """
        self.redmine_url = redmine_url
        self.api_key = api_key
        self.raw_dir = raw_dir
        self.content_dir = content_dir
        self.public_dir = public_dir


def load_config(path: str | Path) -> Config:
    """Load and validate the staticmine YAML configuration file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A validated Config instance.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required fields are missing or the Redmine URL does not
            start with 'https://'.
        yaml.YAMLError: If the file is not valid YAML.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a YAML mapping at the top level.")

    redmine_section = data.get("redmine")
    if not isinstance(redmine_section, dict):
        raise ValueError("Missing required section: 'redmine'")

    redmine_url: Any = redmine_section.get("url")
    if not redmine_url:
        raise ValueError("Missing required field: 'redmine.url'")
    if not isinstance(redmine_url, str):
        raise ValueError("'redmine.url' must be a string.")
    if not redmine_url.startswith("https://"):
        raise ValueError(f"'redmine.url' must start with 'https://'. Got: '{redmine_url}'")

    api_key: Any = redmine_section.get("api_key")
    if not api_key:
        raise ValueError("Missing required field: 'redmine.api_key'")
    if not isinstance(api_key, str):
        raise ValueError("'redmine.api_key' must be a string.")

    output_section = data.get("output", {})
    if not isinstance(output_section, dict):
        output_section = {}

    raw_dir = str(output_section.get("raw", DEFAULT_RAW_DIR))
    content_dir = str(output_section.get("content", DEFAULT_CONTENT_DIR))
    public_dir = str(output_section.get("public", DEFAULT_PUBLIC_DIR))

    return Config(
        redmine_url=redmine_url,
        api_key=api_key,
        raw_dir=raw_dir,
        content_dir=content_dir,
        public_dir=public_dir,
    )
