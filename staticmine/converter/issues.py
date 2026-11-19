"""Converter: generate Hugo content files from raw issue JSON."""

import json
import logging
from pathlib import Path
from typing import Any

from staticmine.converter.frontmatter import field

logger = logging.getLogger(__name__)

_PLACEHOLDER_BODY = "詳細は準備中です。"


def _build_frontmatter(issue: dict[str, Any], project_is_public: bool) -> str:
    """Build the YAML frontmatter string for an issue.

    Fields are written in a fixed order to ensure idempotent output.

    Args:
        issue: A dict representing a single issue from raw/projects/<identifier>/issues.json.
        project_is_public: Whether the parent project is public.

    Returns:
        A string containing the full page content (frontmatter block + body).
    """
    issue_id = issue.get("id", 0)
    title = issue.get("subject", "")
    status = issue.get("status", {}).get("name", "")
    tracker = issue.get("tracker", {}).get("name", "")
    priority = issue.get("priority", {}).get("name", "")
    created_on = issue.get("created_on", "")
    updated_on = issue.get("updated_on", "")
    project_identifier = issue.get("project", {}).get("identifier", "")

    lines = [
        "---",
        field("id", issue_id),
        field("title", title),
        field("status", status),
        field("tracker", tracker),
        field("priority", priority),
        field("created_on", created_on),
        field("updated_on", updated_on),
        field("project_identifier", project_identifier),
        field("project_is_public", project_is_public),
        'type: "issues"',
        "---",
        "",
        _PLACEHOLDER_BODY,
        "",
    ]
    return "\n".join(lines)


def _build_section_index() -> str:
    """Build the content for the issues section _index.md.

    Returns:
        A string with the YAML frontmatter for the issues section page.
    """
    return '---\ntitle: "Issues"\ntype: "issues"\n---\n'


def convert_issues(raw_dir: Path, content_dir: Path) -> None:
    """Convert raw issue JSON into Hugo Page Bundle content files.

    Reads raw_dir/projects.json for the project list and
    raw_dir/projects/<identifier>/issues.json for each project's issues.
    Generates:
    - content_dir/projects/<identifier>/issues/_index.md (section page)
    - content_dir/projects/<identifier>/issues/<id>/index.md (Page Bundle per issue)

    If a target file already exists and its content is identical,
    the write is skipped to preserve timestamps (idempotency).

    Args:
        raw_dir: Directory containing raw/projects.json and raw/projects/<id>/issues.json.
        content_dir: Root content output directory.

    Raises:
        FileNotFoundError: If raw_dir/projects.json does not exist.
        json.JSONDecodeError: If any JSON file contains invalid JSON.
    """
    projects_json = raw_dir / "projects.json"
    if not projects_json.exists():
        raise FileNotFoundError(f"raw projects file not found: {projects_json}")

    with projects_json.open(encoding="utf-8") as f:
        projects: list[dict[str, Any]] = json.load(f)

    # Build identifier -> is_public mapping
    is_public_map: dict[str, bool] = {}
    for project in projects:
        identifier = project.get("identifier")
        if identifier:
            is_public_map[str(identifier)] = bool(project.get("is_public", False))

    written = 0
    skipped = 0

    for project in projects:
        identifier = project.get("identifier")
        if not identifier:
            logger.warning("Skipping project with missing identifier: %s", project)
            skipped += 1
            continue

        identifier_str = str(identifier)
        issues_json_path = raw_dir / "projects" / identifier_str / "issues.json"
        if not issues_json_path.exists():
            logger.warning("No issues.json found for project '%s', skipping.", identifier_str)
            skipped += 1
            continue

        with issues_json_path.open(encoding="utf-8") as f:
            issues_data: dict[str, Any] = json.load(f)

        issues: list[dict[str, Any]] = issues_data.get("issues", [])

        # Generate _index.md for the issues section
        issues_dir = content_dir / "projects" / identifier_str / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        section_index_path = issues_dir / "_index.md"
        section_content = _build_section_index()
        if section_index_path.exists():
            existing: str | None = section_index_path.read_text(encoding="utf-8")
        else:
            existing = None
        if existing != section_content:
            section_index_path.write_text(section_content, encoding="utf-8")
            logger.info("Wrote: %s", section_index_path)
            written += 1
        else:
            logger.debug("Skipping unchanged: %s", section_index_path)
            skipped += 1

        project_is_public = is_public_map.get(identifier_str, False)

        for issue in issues:
            issue_id = issue.get("id")
            if issue_id is None:
                logger.warning("Skipping issue with missing id in project '%s'", identifier_str)
                skipped += 1
                continue

            owner = issue.get("project", {}).get("identifier")
            if owner is not None and str(owner) != identifier_str:
                # Subproject issue included by Redmine; it belongs to its own project.
                logger.debug(
                    "Skipping issue #%s owned by project '%s' under '%s'",
                    issue_id,
                    owner,
                    identifier_str,
                )
                skipped += 1
                continue

            output_dir = issues_dir / str(issue_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "index.md"

            content = _build_frontmatter(issue, project_is_public)

            if output_path.exists() and output_path.read_text(encoding="utf-8") == content:
                logger.debug("Skipping unchanged: %s", output_path)
                skipped += 1
                continue

            output_path.write_text(content, encoding="utf-8")
            logger.info("Wrote: %s", output_path)
            written += 1

        logger.info(
            "Converted %d issues for project '%s'",
            len(issues),
            identifier_str,
        )

    logger.info(
        "Convert issues complete: %d written, %d skipped",
        written,
        skipped,
    )
