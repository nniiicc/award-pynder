"""Shared Algolia search helper for sources using Algolia-backed search."""

from __future__ import annotations

import requests

###############################################################################

_ALGOLIA_URL_TEMPLATE = "https://{app_id}-dsn.algolia.net/1/indexes/*/queries"

_ALGOLIA_AGENT = (
    "Algolia for JavaScript (4.5.1); Browser (lite); "
    "instantsearch.js (4.8.3); JS Helper (3.2.2)"
)

###############################################################################


def algolia_search(
    app_id: str,
    api_key: str,
    index_name: str,
    params: str,
    page: int = 0,
) -> dict:
    """Execute a single Algolia search query and return the JSON response.

    Parameters
    ----------
    app_id : str
        The Algolia application ID.
    api_key : str
        The Algolia public API key.
    index_name : str
        The Algolia index name to search.
    params : str
        URL-encoded query parameters string.
    page : int
        The page number to fetch (0-indexed).

    Returns
    -------
    dict
        The parsed JSON response from Algolia.
    """
    url = _ALGOLIA_URL_TEMPLATE.format(app_id=app_id.lower())
    url += (
        f"?x-algolia-agent={_ALGOLIA_AGENT}"
        f"&x-algolia-api-key={api_key}"
        f"&x-algolia-application-id={app_id}"
    )

    payload = {
        "requests": [
            {
                "indexName": index_name,
                "params": f"{params}&page={page}",
            }
        ]
    }

    resp = requests.post(url, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()
