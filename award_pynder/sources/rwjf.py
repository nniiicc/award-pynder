#!/usr/bin/env python

from __future__ import annotations

import logging
import time
from datetime import datetime

import pandas as pd
import requests
from tqdm import tqdm

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_RWJF_API_URL = "https://www.rwjf.org/content/rwjf-web/us/en/_jcr_content.grants.json"
_DEFAULT_CHUNK_SIZE = 20

###############################################################################


class RWJF(DataSource):
    """Data source for the Robert Wood Johnson Foundation."""

    @staticmethod
    def _format_query_url(
        query: str | None,
        from_year: int | None,
        to_year: int | None,
        page: int = 1,
    ) -> str:
        url = f"{_RWJF_API_URL}?"
        if query:
            url += f"k={query.replace(' ', '%20')}"
        if from_year:
            url += f"&start={from_year}"
        if to_year:
            url += f"&end={to_year}"
        url += (
            "&ff=tags_sm&m="
            "&active=true&closed=true"
            "&sortBy=year&ascending=false"
            f"&s={page}"
        )
        return url

    @staticmethod
    def _extract_director(contacts: list[dict]) -> str | None:
        """Extract project director name from contacts list."""
        if not contacts:
            return None
        directors = [
            c.get("name", "") for c in contacts if c.get("title") == "Project Director"
        ]
        return "; ".join(directors) if directors else None

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "RWJF"

        # Rename columns
        df = df.rename(
            columns={
                "orgName": DatasetFields.institution,
                "director": DatasetFields.pi,
                "grantNumber": DatasetFields.id_,
                "title": DatasetFields.title,
                "description": DatasetFields.abstract,
                "amountAwarded": DatasetFields.amount,
            }
        )

        # Add missing columns
        for field in ALL_DATASET_FIELDS:
            if field not in df.columns:
                df[field] = None

        return df[ALL_DATASET_FIELDS]

    @staticmethod
    def get_data(  # noqa: C901
        query: str | None = None,
        from_datetime: str | datetime | None = None,
        to_datetime: str | datetime | None = None,
        raise_on_error: bool = True,
        tqdm_kwargs: dict | None = None,
    ) -> pd.DataFrame:
        """
        Get data from the Robert Wood Johnson Foundation.

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
            All grants from RWJF for the specified time period and query,
            formatted into award_pynder standard format.
        """
        from_year = None
        to_year = None
        if from_datetime:
            from_year = DataSource._parse_datetime(from_datetime).year
        if to_datetime:
            to_year = DataSource._parse_datetime(to_datetime).year

        try:
            # First page to get total
            url = RWJF._format_query_url(query, from_year, to_year, page=1)
            resp = requests.get(url, timeout=300)
            resp.raise_for_status()
            data = resp.json()

            if data.get("totalResults", 0) == 0:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            total_pages = data.get("totalPages", 1)
            all_results = data.get("results", [])

            # Fetch remaining pages
            for page in tqdm(
                range(2, total_pages + 1),
                desc="Fetching RWJF data",
                **(tqdm_kwargs or {}),
            ):
                url = RWJF._format_query_url(query, from_year, to_year, page=page)
                resp = requests.get(url, timeout=300)
                resp.raise_for_status()
                page_data = resp.json()
                all_results.extend(page_data.get("results", []))
                time.sleep(1)

            # Process results
            rows = []
            for item in all_results:
                # Convert millisecond timestamps to dates
                date_awarded = item.get("dateAwarded")
                start_date = item.get("startDate")
                end_date = item.get("endDate")

                year = None
                start_str = None
                end_str = None

                if date_awarded:
                    dt = datetime.fromtimestamp(date_awarded / 1000)
                    year = dt.year
                if start_date:
                    start_str = (
                        datetime.fromtimestamp(start_date / 1000).date().isoformat()
                    )
                if end_date:
                    end_str = datetime.fromtimestamp(end_date / 1000).date().isoformat()

                director = RWJF._extract_director(item.get("contact", []))

                rows.append(
                    {
                        "orgName": item.get("granteeInfo", {}).get("orgName"),
                        "director": director,
                        DatasetFields.year: year,
                        DatasetFields.start: start_str,
                        DatasetFields.end: end_str,
                        "grantNumber": item.get("grantNumber"),
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "amountAwarded": item.get("amountAwarded"),
                    }
                )

            if not rows:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            df = pd.DataFrame(rows)
            return RWJF._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching RWJF data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
