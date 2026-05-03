"""Fetcher for Redmine project list."""

import json
import logging
from pathlib import Path
from typing import Any

from redminelib import Redmine

logger = logging.getLogger(__name__)

_FIELDS = ("id", "identifier", "name", "description", "is_public", "created_on", "updated_on")


def _serialize_project(project: Any) -> dict[str, Any]:
    """Serialize a Redmine project resource to a plain dict.

    Args:
        project: A python-redmine Project resource object.

    Returns:
        A dict containing the project's fields.
    """
    data: dict[str, Any] = {}
    for field in _FIELDS:
        value = getattr(project, field, None)
        if value is not None:
            # Convert datetime objects to ISO 8601 strings
            if hasattr(value, "isoformat"):
                data[field] = value.isoformat()
            else:
                data[field] = value

    # parent_id is optional
    try:
        parent = getattr(project, "parent", None)
        if parent is not None:
            parent_id = getattr(parent, "id", None)
            if parent_id is not None:
                data["parent_id"] = parent_id
    except Exception:
        pass

    return data


def fetch_projects(redmine_url: str, api_key: str, raw_dir: Path) -> None:
    """Fetch all Redmine projects and save them as raw/projects.json.

    Connects to Redmine using the given URL and API key, retrieves all
    accessible projects, and writes a JSON array to ``raw_dir/projects.json``.

    Args:
        redmine_url: The Redmine base URL (must use HTTPS).
        api_key: The Redmine API key.
        raw_dir: The directory where raw JSON files are stored.

    Raises:
        ValueError: If redmine_url does not start with 'https://'.
        OSError: If the output file cannot be written.
    """
    if not redmine_url.startswith("https://"):
        raise ValueError(f"redmine_url must start with 'https://'. Got: '{redmine_url}'")

    raw_dir.mkdir(parents=True, exist_ok=True)

    redmine = Redmine(redmine_url, key=api_key)
    projects = redmine.project.all()

    project_list = [_serialize_project(p) for p in projects]

    output_path = raw_dir / "projects.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(project_list, f, indent=2, ensure_ascii=False)

    logger.info("Fetched %d projects -> %s", len(project_list), output_path)
