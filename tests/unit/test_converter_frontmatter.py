"""Unit tests for frontmatter escaping in converters."""

import json
from pathlib import Path

import pytest
import yaml

from staticmine.converter import issues as issues_conv
from staticmine.converter import projects as projects_conv
from staticmine.converter.frontmatter import field, yaml_str

TRICKY_STRINGS = [
    'He said "hello"',
    "back\\slash",
    "line1\nline2",
    "tab\there",
    "colon: value # not a comment",
    "- leading dash",
    "true",
    "123",
    "'single'",
    "日本語の名前",
    "ctrl\x07\x7f\x85\u2028",
    "x" * 300,
]


def _parse_frontmatter(text: str) -> dict:
    parts = text.split("---\n")
    # parts[0] is empty (before the opening delimiter), parts[1] is the YAML body
    data = yaml.safe_load(parts[1])
    assert isinstance(data, dict)
    return data


@pytest.mark.parametrize("value", TRICKY_STRINGS)
def test_yaml_str_round_trips(value: str) -> None:
    """yaml_str output must parse back to the original string on a single line."""
    rendered = yaml_str(value)
    assert "\n" not in rendered
    assert yaml.safe_load(f"k: {rendered}") == {"k": value}


def test_field_scalar_types() -> None:
    assert field("id", 5) == "id: 5"
    assert field("flag", True) == "flag: true"
    assert field("flag", False) == "flag: false"
    assert field("name", "My Project") == 'name: "My Project"'


@pytest.mark.parametrize("value", TRICKY_STRINGS)
def test_project_frontmatter_is_valid_yaml(value: str) -> None:
    parent = {"id": 1, "identifier": "parent", "name": value}
    project = {
        "id": 2,
        "identifier": "child",
        "name": value,
        "is_public": True,
        "created_on": "2021-01-01T00:00:00Z",
        "parent_id": 1,
    }
    result = projects_conv._build_frontmatter(project, {1: parent, 2: project})
    data = _parse_frontmatter(result)
    assert data["name"] == value
    assert data["parent_name"] == value
    assert data["id"] == 2
    assert data["created_on"] == "2021-01-01T00:00:00Z"


@pytest.mark.parametrize("value", TRICKY_STRINGS)
def test_issue_frontmatter_is_valid_yaml(value: str) -> None:
    issue = {
        "id": 10,
        "project": {"identifier": "alpha"},
        "subject": value,
        "status": {"name": value},
        "tracker": {"name": "Bug"},
        "priority": {"name": "Normal"},
        "created_on": "2021-01-15T10:00:00Z",
        "updated_on": "2021-02-01T09:30:00Z",
    }
    data = _parse_frontmatter(issues_conv._build_frontmatter(issue, True))
    assert data["title"] == value
    assert data["status"] == value
    assert data["id"] == 10
    assert data["project_is_public"] is True


def test_convert_projects_writes_parseable_file_for_quoted_name(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    projects = [{"id": 1, "identifier": "q", "name": 'A "quoted" name', "is_public": True}]
    (raw_dir / "projects.json").write_text(json.dumps(projects), encoding="utf-8")

    projects_conv.convert_projects(raw_dir, tmp_path / "content")

    text = (tmp_path / "content" / "projects" / "q" / "_index.md").read_text(encoding="utf-8")
    assert _parse_frontmatter(text)["name"] == 'A "quoted" name'
