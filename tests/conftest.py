"""Shared pytest fixtures and VCR.py configuration."""

import pytest


def _filter_request_headers(request: object) -> object:
    """Remove sensitive headers from VCR request recording.

    Args:
        request: The VCR request object.

    Returns:
        The modified request object with sensitive headers removed.
    """
    if hasattr(request, "headers"):
        request.headers.pop("X-Redmine-API-Key", None)  # type: ignore[union-attr]
    return request


def _filter_uri(uri: str) -> str:
    """Replace real Redmine host with a placeholder in VCR cassettes.

    Args:
        uri: The original URI string.

    Returns:
        The URI with the hostname replaced by 'redmine.example.com'.
    """
    import re

    return re.sub(r"https?://[^/]+", "https://redmine.example.com", uri)


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    """VCR.py configuration: mask API key and hostname.

    Returns:
        A dict of VCR configuration options.
    """
    return {
        "before_record_request": _filter_request_headers,
        "before_record_response": None,
        "filter_query_parameters": ["key"],
        "decode_compressed_response": True,
    }
