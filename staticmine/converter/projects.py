"""Converter: generate Hugo content files from raw project JSON."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FRONTMATTER_FIELDS = (
    "id",
    "identifier",
    "name",
    "project_is_public",
    "created_on",
    "parent_identifier",
    "parent_name",
)


def _build_frontmatter(
    project: dict[str, Any], id_to_project: dict[int, dict[str, Any]]
) -> str:
    """Build the YAML frontmatter string for a project.

    Fields are written in a fixed order to ensure idempotent output.

    Args:
        project: A dict representing a single project from raw/projects.json.
        id_to_project: A mapping from project id to project dict, used to
            resolve parent_id to parent_identifier / parent_name.

    Returns:
        A string containing the frontmatter block (including delimiters).
    """
    project_id = project.get("id", "")
    identifier = project.get("identifier", "")
    name = project.get("name", "")
    project_is_public = project.get("is_public", False)
    created_on = project.get("created_on", "")

    lines = [
        "---",
        f"id: {project_id}",
        f'identifier: "{identifier}"',
        f'name: "{name}"',
        f"project_is_public: {'true' if project_is_public else 'false'}",
        f'created_on: "{created_on}"',
    ]

    parent_id = project.get("parent_id")
    if parent_id is not None:
        parent = id_to_project.get(parent_id)
        if parent is not None:
            parent_identifier = parent.get("identifier", "")
            parent_name = parent.get("name", "")
            lines.append(f'parent_identifier: "{parent_identifier}"')
            lines.append(f'parent_name: "{parent_name}"')
        else:
            logger.warning(
                "parent_id %s not found in project list for project '%s'; "
                "skipping parent_identifier / parent_name",
                parent_id,
                identifier,
            )

    lines += ["---", ""]
    return "\n".join(lines)


def convert_projects(raw_dir: Path, content_dir: Path) -> None:
    """Convert raw/projects.json into Hugo content files.

    Reads ``raw_dir/projects.json`` and generates
    ``content_dir/projects/<identifier>/_index.md`` for each project.
    If the target file already exists and its content is identical,
    the write is skipped to preserve timestamps (idempotency).

    Args:
        raw_dir: Directory containing raw/projects.json.
        content_dir: Root content output directory.

    Raises:
        FileNotFoundError: If raw_dir/projects.json does not exist.
        json.JSONDecodeError: If projects.json contains invalid JSON.
    """
    projects_json = raw_dir / "projects.json"
    if not projects_json.exists():
        raise FileNotFoundError(f"raw projects file not found: {projects_json}")

    with projects_json.open(encoding="utf-8") as f:
        projects: list[dict[str, Any]] = json.load(f)

    id_to_project: dict[int, dict[str, Any]] = {
        p["id"]: p for p in projects if "id" in p
    }

    written = 0
    skipped = 0

    for project in projects:
        identifier = project.get("identifier")
        if not identifier:
            logger.warning("Skipping project with missing identifier: %s", project)
            skipped += 1
            continue

        output_dir = content_dir / "projects" / str(identifier)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "_index.md"

        content = _build_frontmatter(project, id_to_project)
        body = project.get("description", "").strip()
        if body:
            content += body + "\n"

        if output_path.exists() and output_path.read_text(encoding="utf-8") == content:
            logger.debug("Skipping unchanged: %s", output_path)
            skipped += 1
            continue

        output_path.write_text(content, encoding="utf-8")
        logger.info("Wrote: %s", output_path)
        written += 1

    logger.info(
        "Convert complete: %d written, %d skipped (total %d projects)",
        written,
        skipped,
        len(projects),
    )
