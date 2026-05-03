"""Command-line interface for staticmine."""

import logging
import subprocess
import sys
from pathlib import Path

import click

from staticmine.config.loader import load_config
from staticmine.converter.projects import convert_projects
from staticmine.fetcher.projects import fetch_projects

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main() -> None:
    """staticmine: Convert Redmine data to a static HTML site."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@main.command()
@click.option(
    "--config",
    "config_path",
    default="staticmine.yaml",
    show_default=True,
    help="Path to the configuration YAML file.",
)
@click.option(
    "--out",
    "out_dir",
    default=None,
    help="Output directory for raw JSON (overrides config output.raw).",
)
def fetch(config_path: str, out_dir: str | None) -> None:
    """Fetch project data from Redmine and save to raw/.

    Reads the configuration file, connects to Redmine via its REST API,
    and writes raw JSON to the configured output directory.
    """
    cfg = load_config(config_path)
    raw_dir = out_dir if out_dir is not None else cfg.raw_dir
    fetch_projects(cfg.redmine_url, cfg.api_key, Path(raw_dir))
    click.echo(f"Fetch complete. Output: {raw_dir}")


@main.command()
@click.option(
    "--config",
    "config_path",
    default="staticmine.yaml",
    show_default=True,
    help="Path to the configuration YAML file.",
)
@click.option(
    "--in",
    "in_dir",
    default=None,
    help="Input directory of raw JSON (overrides config output.raw).",
)
@click.option(
    "--out",
    "out_dir",
    default=None,
    help="Output directory for Markdown content (overrides config output.content).",
)
def convert(config_path: str, in_dir: str | None, out_dir: str | None) -> None:
    """Convert raw JSON to Markdown content files.

    Reads raw/projects.json and generates content/projects/<identifier>/_index.md
    for each project. This command does not require a network connection.

    When both --in and --out are specified, the configuration file is not required.
    When either or both are omitted, the configuration file is read to supply defaults.
    """
    if in_dir is not None and out_dir is not None:
        raw_dir = in_dir
        content_dir = out_dir
    else:
        cfg = load_config(config_path)
        raw_dir = in_dir if in_dir is not None else cfg.raw_dir
        content_dir = out_dir if out_dir is not None else cfg.content_dir
    convert_projects(Path(raw_dir), Path(content_dir))
    click.echo(f"Convert complete. Output: {content_dir}")


@main.command()
@click.option(
    "--config",
    "config_path",
    default="staticmine.yaml",
    show_default=True,
    help="Path to the configuration YAML file.",
)
@click.option(
    "--in",
    "in_dir",
    default=None,
    help="Content directory to build from (overrides config output.content).",
)
@click.option(
    "--out",
    "out_dir",
    default=None,
    help="Output directory for the built site (overrides config output.public).",
)
def build(config_path: str, in_dir: str | None, out_dir: str | None) -> None:
    """Build the static site using Hugo.

    Runs Hugo with the content directory and outputs to public/.
    Requires the 'hugo' binary to be available in PATH.

    When both --in and --out are specified, the configuration file is not required.
    When either or both are omitted, the configuration file is read to supply defaults.
    """
    if in_dir is not None and out_dir is not None:
        content_dir = in_dir
        public_dir = out_dir
    else:
        cfg = load_config(config_path)
        content_dir = in_dir if in_dir is not None else cfg.content_dir
        public_dir = out_dir if out_dir is not None else cfg.public_dir

    content_abs = str(Path(content_dir).resolve())
    public_abs = str(Path(public_dir).resolve())

    cmd = [
        "hugo",
        "--source",
        "hugo/",
        "--contentDir",
        content_abs,
        "--destination",
        public_abs,
    ]

    logger.info("Running Hugo: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        if result.returncode != 0:
            logger.error("Hugo exited with code %d", result.returncode)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo(
            "Error: 'hugo' command not found. Please install Hugo extended and add it to PATH.\n"
            "  https://gohugo.io/installation/",
            err=True,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        logger.error("Hugo build failed: %s", exc)
        sys.exit(exc.returncode)

    click.echo(f"Build complete. Output: {public_dir}")
