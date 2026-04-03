"""Shared utilities for the award_pynder package."""

from __future__ import annotations

import hashlib
import logging

import requests

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_DEFAULT_TIMEOUT = 300


def http_request(
    url: str,
    method: str = "get",
    json: dict | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
    **kwargs: object,
) -> requests.Response:
    """Make an HTTP request with standard timeout and error handling.

    Parameters
    ----------
    url : str
        The URL to request.
    method : str
        HTTP method ("get" or "post").
    json : dict, optional
        JSON payload for POST requests.
    timeout : int
        Request timeout in seconds.
    **kwargs
        Additional keyword arguments passed to requests.

    Returns
    -------
    requests.Response
        The HTTP response.

    Raises
    ------
    requests.HTTPError
        If the response status code indicates an error.
    """
    resp = requests.request(
        method=method.upper(),
        url=url,
        json=json,
        timeout=timeout,
        **kwargs,
    )
    resp.raise_for_status()
    return resp


def text_hash(text: str) -> str:
    """Generate a deterministic short hash from text for use as a grant ID.

    Parameters
    ----------
    text : str
        The text to hash.

    Returns
    -------
    str
        A 16-character hex digest.
    """
    return hashlib.md5(text.encode()).hexdigest()[:16]
