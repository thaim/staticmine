"""Shared helpers for emitting Hugo YAML frontmatter."""

from typing import Any

import yaml


def yaml_str(value: str) -> str:
    """Render a string as a YAML double-quoted scalar.

    PyYAML handles escaping of quotes, backslashes, line breaks and
    non-printable characters, so arbitrary Redmine text yields valid YAML.
    The result never wraps, keeping one field per line.

    Args:
        value: The string to render.

    Returns:
        The double-quoted scalar without a trailing newline.
    """
    dumped: str = yaml.dump(value, default_style='"', allow_unicode=True, width=float("inf"))
    return dumped.rstrip("\n")


def field(key: str, value: Any) -> str:
    """Render a single ``key: value`` frontmatter line.

    Args:
        key: The frontmatter key (must be a plain YAML key).
        value: A str, bool or int value.

    Returns:
        The rendered line.
    """
    if isinstance(value, bool):
        return f"{key}: {'true' if value else 'false'}"
    if isinstance(value, int):
        return f"{key}: {value}"
    return f"{key}: {yaml_str(str(value))}"
