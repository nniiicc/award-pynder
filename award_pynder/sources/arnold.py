#!/usr/bin/env python

from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import quote

import pandas as pd

from ._algolia import algolia_search
from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_ALGOLIA_APP_ID = "PYJ9B8SLTV"
_ALGOLIA_API_KEY = "d24384ea1c21933773c3f88fa6f605ea"
_ALGOLIA_INDEX = "grants"

###############################################################################


class Arnold(DataSource):
    """Data source for Arnold Ventures."""

    @staticmethod
    def _build_params(
        query: str | None,
        from_year: int | None,
        to_year: int | None,
    ) -> str:
        """Build URL-encoded Algolia query params string."""
        parts = []
        if query:
            parts.append(f"query={query}")
        else:
            parts.append("query=")

        parts.append("maxValuesPerFacet=100")
        parts.append("highlightPreTag=__ais-highlight__")
        parts.append("highlightPostTag=__%2Fais-highlight__")
        parts.append("facets=%5B%22topics%22%2C%22years%22%2C%22fundingSource%22%5D")
        parts.append("tagFilters=")

        # Build year facet filter
        if from_year and to_year:
            year_filters = ",".join(
                f'"years:{y}"' for y in range(from_year, to_year + 1)
            )
            parts.append(f"facetFilters=%5B%5B{quote(year_filters)}%5D%5D")

        return "&".join(parts)

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Extract year and dates from grantTerm
        if "grantTerm" in df.columns:
            df[DatasetFields.year] = df["grantTerm"].apply(
                lambda x: int(str(x)[:4]) if pd.notna(x) and len(str(x)) >= 4 else None
            )
            df[DatasetFields.start] = df["grantTerm"].apply(
                lambda x: str(x)[:4] if pd.notna(x) and len(str(x)) >= 4 else None
            )
            df[DatasetFields.end] = df["grantTerm"].apply(
                lambda x: str(x)[-4:] if pd.notna(x) and len(str(x)) >= 4 else None
            )

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "Arnold"

        # Rename columns
        df = df.rename(
            columns={
                "title": DatasetFields.institution,
                "grantDescription": DatasetFields.title,
                "fundingSource": DatasetFields.program,
                "grantAmount": DatasetFields.amount,
                "objectID": DatasetFields.id_,
            }
        )

        # Add missing columns
        for field in ALL_DATASET_FIELDS:
            if field not in df.columns:
                df[field] = None

        return df[ALL_DATASET_FIELDS]

    @staticmethod
    def get_data(
        query: str | None = None,
        from_datetime: str | datetime | None = None,
        to_datetime: str | datetime | None = None,
        raise_on_error: bool = True,
        tqdm_kwargs: dict | None = None,
    ) -> pd.DataFrame:
        """
        Get data from Arnold Ventures.

        Parameters
        ----------
        query : str, optional
            The query string to search for.
        from_datetime : str or datetime, optional
            The start date for the search.
        to_datetime : str or datetime, optional
            The end date for the search.
        raise_on_error : bool, optional
            Whether to raise an error if the request fails.
        tqdm_kwargs : dict, optional
            Keyword arguments to pass to tqdm.

        Returns
        -------
        pd.DataFrame
            All grants from Arnold Ventures for the specified time period
            and query, formatted into award_pynder standard format.
        """
        from_year = None
        to_year = None
        if from_datetime:
            from_year = DataSource._parse_datetime(from_datetime).year
        if to_datetime:
            to_year = DataSource._parse_datetime(to_datetime).year

        try:
            params = Arnold._build_params(query, from_year, to_year)

            # First page
            response = algolia_search(
                app_id=_ALGOLIA_APP_ID,
                api_key=_ALGOLIA_API_KEY,
                index_name=_ALGOLIA_INDEX,
                params=params,
                page=0,
            )

            results = response.get("results", [{}])[0]
            if results.get("nbHits", 0) == 0:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            all_hits = list(results.get("hits", []))
            nb_pages = results.get("nbPages", 1)

            # Fetch remaining pages
            for page in range(1, nb_pages):
                response = algolia_search(
                    app_id=_ALGOLIA_APP_ID,
                    api_key=_ALGOLIA_API_KEY,
                    index_name=_ALGOLIA_INDEX,
                    params=params,
                    page=page,
                )
                page_results = response.get("results", [{}])[0]
                all_hits.extend(page_results.get("hits", []))

            if not all_hits:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            # Extract relevant fields
            rows = []
            for hit in all_hits:
                rows.append(
                    {
                        "title": hit.get("title"),
                        "grantDescription": hit.get("grantDescription"),
                        "grantTerm": hit.get("grantTerm"),
                        "fundingSource": hit.get("fundingSource"),
                        "grantAmount": hit.get("grantAmount"),
                        "objectID": str(hit.get("objectID")),
                    }
                )

            df = pd.DataFrame(rows)
            return Arnold._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching Arnold data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
