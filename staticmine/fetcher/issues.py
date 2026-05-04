"""Fetcher for Redmine issue list."""

import json
import logging
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

PAGE_SIZE = 100


def _fetch_issues_for_project(
    redmine_url: str, api_key: str, identifier: str
) -> list[dict[str, Any]]:
    """Fetch all issues for a single project using offset/limit pagination.

    Args:
        redmine_url: The Redmine base URL.
        api_key: The Redmine API key.
        identifier: The project identifier string.

    Returns:
        A list of issue dicts containing all pages of results.
    """
    issues: list[dict[str, Any]] = []
    offset = 0

    while True:
        url = f"{redmine_url}/issues.json"
        params: dict[str, Any] = {
            "project_id": identifier,
            "status_id": "*",
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        headers = {"X-Redmine-API-Key": api_key}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        page_issues: list[dict[str, Any]] = data.get("issues", [])
        issues.extend(page_issues)

        total_count: int = data.get("total_count", 0)
        offset += len(page_issues)

        logger.debug(
            "Fetched %d/%d issues for project '%s' (offset=%d)",
            len(issues),
            total_count,
            identifier,
            offset,
        )

        if offset >= total_count or not page_issues:
            break

    return issues


def fetch_issues(redmine_url: str, api_key: str, raw_dir: Path) -> None:
    """Fetch all issues for each project and save them as raw/projects/<identifier>/issues.json.

    Reads the project list from raw_dir/projects.json, then for each project,
    fetches all issues using offset/limit pagination and saves the result.

    Args:
        redmine_url: The Redmine base URL (must use HTTPS).
        api_key: The Redmine API key.
        raw_dir: The directory where raw JSON files are stored.

    Raises:
        ValueError: If redmine_url does not start with 'https://'.
        FileNotFoundError: If raw_dir/projects.json does not exist.
        requests.HTTPError: If the Redmine API returns an error response.
    """
    if not redmine_url.startswith("https://"):
        raise ValueError(f"redmine_url must start with 'https://'. Got: '{redmine_url}'")

    projects_json = raw_dir / "projects.json"
    if not projects_json.exists():
        raise FileNotFoundError(f"raw projects file not found: {projects_json}")

    with projects_json.open(encoding="utf-8") as f:
        projects: list[dict[str, Any]] = json.load(f)

    for project in projects:
        identifier = project.get("identifier")
        if not identifier:
            logger.warning("Skipping project with missing identifier: %s", project)
            continue

        issues = _fetch_issues_for_project(redmine_url, api_key, str(identifier))

        output_dir = raw_dir / "projects" / str(identifier)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "issues.json"

        payload: dict[str, Any] = {
            "total_count": len(issues),
            "issues": issues,
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info(
            "Fetched %d issues for project '%s' -> %s",
            len(issues),
            identifier,
            output_path,
        )
