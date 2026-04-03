#!/usr/bin/env python

from __future__ import annotations

import logging
import re
from datetime import datetime

import pandas as pd
import requests

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_GATES_API_URL = "https://www.gatesfoundation.org/api/grantssearch"

_DEFAULT_PARAMS = {
    "date": "",
    "displayedTaxonomy": "",
    "listingId": "d2a41504-f557-4f1e-88d6-ea109d344feb",
    "loadAllPages": "true",
    "page": "1",
    "pageId": "31242fca-dcf8-466a-a296-d6411f85b0a5",
    "perPage": "999",
    "sc_site": "gfo",
    "showContentTypes": "false",
    "showDates": "false",
    "showImages": "",
    "showSummaries": "false",
    "sortBy": "date-desc",
    "sortOrder": "desc",
}

###############################################################################


class Gates(DataSource):
    """Data source for the Bill & Melinda Gates Foundation."""

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Clean amount: remove $ and commas, convert to float
        if "awardedAmount" in df.columns:
            df[DatasetFields.amount] = df["awardedAmount"].apply(
                lambda x: (
                    float(re.sub(r"[$,]", "", str(x)))
                    if pd.notna(x) and str(x).strip()
                    else None
                )
            )

        # Extract year from date
        if "date" in df.columns:
            df[DatasetFields.year] = df["date"].apply(
                lambda x: int(str(x)[-4:]) if pd.notna(x) else None
            )

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "Gates"

        # Rename columns
        df = df.rename(
            columns={
                "grantee": DatasetFields.institution,
                "url": DatasetFields.id_,
            }
        )

        # Replace empty grantees with None
        if DatasetFields.institution in df.columns:
            df[DatasetFields.institution] = df[DatasetFields.institution].replace(
                "", None
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
        Get data from the Bill & Melinda Gates Foundation.

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
            All grants from the Gates Foundation for the specified time
            period and query, formatted into award_pynder standard format.
        """
        try:
            params = dict(_DEFAULT_PARAMS)
            if query:
                params["q"] = query
            if from_datetime:
                from_dt = DataSource._parse_datetime(from_datetime)
                params["yearAwardedStart"] = str(from_dt.year)
            if to_datetime:
                to_dt = DataSource._parse_datetime(to_datetime)
                params["yearAwardedEnd"] = str(to_dt.year)

            resp = requests.get(_GATES_API_URL, params=params, timeout=300)

            # Check if we got HTML instead of JSON (error page)
            content_type = resp.headers.get("content-type", "")
            if "html" in content_type:
                log.warning("Gates API returned HTML instead of JSON")
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            resp.raise_for_status()
            data = resp.json()

            if data.get("totalResults", 0) == 0:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            # Extract results
            results = data.get("results", [])
            rows = []
            for item in results:
                # Use url as ID (matching R package), not the API's id field
                row = {
                    "awardedAmount": item.get("awardedAmount"),
                    "grantee": item.get("grantee"),
                    "url": item.get("url"),
                    "date": item.get("date"),
                }
                rows.append(row)

            if not rows:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            df = pd.DataFrame(rows)
            return Gates._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching Gates data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
