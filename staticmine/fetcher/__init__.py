"""Fetcher module for staticmine."""

from staticmine.fetcher.issues import fetch_issues
from staticmine.fetcher.projects import fetch_projects

__all__ = ["fetch_issues", "fetch_projects"]
