#!/usr/bin/env python

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from ._algolia import algolia_search
from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_ALGOLIA_APP_ID = "12786HBSDL"
_ALGOLIA_API_KEY = "cdd85ab4fc628277674bb5d9e375af2b"
_ALGOLIA_INDEX = "wp_searchable_posts"

###############################################################################


class SSRC(DataSource):
    """Data source for the Social Science Research Council."""

    @staticmethod
    def _build_params(
        query: str | None,
        from_year: int | None,
        to_year: int | None,
    ) -> str:
        """Build URL-encoded Algolia query params string."""
        parts = []
        if query:
            parts.append(f'query="{query}"')
        else:
            parts.append("query=")

        # Build year + post_type facet filters
        if from_year and to_year:
            year_filters = ",".join(
                f'"competition_year:{y}"' for y in range(from_year, to_year + 1)
            )
            facet = f'[[{year_filters}],["post_type:fellow"]]'
        else:
            facet = '[["post_type:fellow"]]'

        parts.append(f"facetFilters={facet}")
        return "&".join(parts)

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Format start date from Unix timestamp
        if "post_date" in df.columns:
            df[DatasetFields.start] = df["post_date"].apply(
                lambda x: (
                    datetime.fromtimestamp(int(x)).date().isoformat()
                    if pd.notna(x)
                    else None
                )
            )

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "SSRC"

        # Rename columns
        df = df.rename(
            columns={
                "award_institution": DatasetFields.institution,
                "post_title": DatasetFields.pi,
                "competition_year": DatasetFields.year,
                "related_competitions": DatasetFields.program,
                "post_id": DatasetFields.id_,
                "project_title": DatasetFields.title,
                "content": DatasetFields.abstract,
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
        Get data from the Social Science Research Council.

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
            All fellowships from SSRC for the specified time period and
            query, formatted into award_pynder standard format.
        """
        from_year = None
        to_year = None
        if from_datetime:
            from_year = DataSource._parse_datetime(from_datetime).year
        if to_datetime:
            to_year = DataSource._parse_datetime(to_datetime).year

        try:
            params = SSRC._build_params(query, from_year, to_year)

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
                        "post_id": str(hit.get("post_id")),
                        "post_title": hit.get("post_title"),
                        "post_date": hit.get("post_date"),
                        "competition_year": hit.get("competition_year"),
                        "project_title": hit.get("project_title"),
                        "award_institution": hit.get("award_institution"),
                        "related_competitions": hit.get("related_competitions"),
                        "content": hit.get("content"),
                    }
                )

            df = pd.DataFrame(rows)
            return SSRC._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching SSRC data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
