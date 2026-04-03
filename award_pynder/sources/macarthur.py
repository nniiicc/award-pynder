#!/usr/bin/env python

from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import requests

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_MACARTHUR_SOLR_URL = "https://searchg2.crownpeak.net/live-macfound-redesign-rt/select"

###############################################################################


class MacArthur(DataSource):
    """Data source for the MacArthur Foundation."""

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Format start/end dates (truncate to date portion)
        if "custom_s_start_date" in df.columns:
            df[DatasetFields.start] = df["custom_s_start_date"].apply(
                lambda x: str(x)[:10] if pd.notna(x) else None
            )
        if "custom_s_end_date" in df.columns:
            df[DatasetFields.end] = df["custom_s_end_date"].apply(
                lambda x: str(x)[:10] if pd.notna(x) else None
            )

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "MacArthur"

        # Rename columns
        df = df.rename(
            columns={
                "custom_s_name": DatasetFields.institution,
                "custom_i_year_approved": DatasetFields.year,
                "custom_s_program_area_code": DatasetFields.program,
                "custom_s_amount": DatasetFields.amount,
                "id": DatasetFields.id_,
                "custom_s_title": DatasetFields.title,
                "custom_s_description": DatasetFields.abstract,
            }
        )

        # Convert amount to numeric
        if DatasetFields.amount in df.columns:
            df[DatasetFields.amount] = pd.to_numeric(
                df[DatasetFields.amount], errors="coerce"
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
        Get data from the MacArthur Foundation.

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
            All grants from the MacArthur Foundation for the specified time
            period and query, formatted into award_pynder standard format.

        Notes
        -----
        The CrownPeak Solr endpoint used by the R package may have moved.
        If this source returns no results, the endpoint may need updating.
        """
        try:
            params = {
                "q": quote(query) if query else "*:*",
                "wt": "json",
                "start": "0",
                "rows": "25494",
                "echoParams": "explicit",
                "fl": "*",
                "defType": "edismax",
                "fq": 'custom_s_template:"grant detail"',
                "sort": "score desc",
                "qf": "custom_t_title custom_t_description custom_t_name",
            }

            resp = requests.get(_MACARTHUR_SOLR_URL, params=params, timeout=300)
            resp.raise_for_status()
            data = resp.json()

            response_data = data.get("response", {})
            if response_data.get("numFound", 0) == 0:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            results = pd.DataFrame(response_data.get("docs", []))

            # Apply date filtering
            if "custom_i_year_approved" in results.columns:
                if from_datetime:
                    from_year = DataSource._parse_datetime(from_datetime).year
                    results = results[results["custom_i_year_approved"] >= from_year]
                if to_datetime:
                    to_year = DataSource._parse_datetime(to_datetime).year
                    results = results[results["custom_i_year_approved"] <= to_year]

            if results.empty:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            return MacArthur._format_dataframe(results, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching MacArthur data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
