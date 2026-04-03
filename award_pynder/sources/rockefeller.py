#!/usr/bin/env python

from __future__ import annotations

import logging
from datetime import datetime
from io import StringIO

import pandas as pd
import requests

from ..utils import text_hash
from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_ROCKEFELLER_URL = "https://www.rockefellerfoundation.org/"

###############################################################################


class Rockefeller(DataSource):
    """Data source for the Rockefeller Foundation."""

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Generate IDs from all row content for uniqueness
        def _make_id(row: pd.Series) -> str:
            parts = [
                str(row.get("Title", "")),
                str(row.get("Description", "")),
                str(row.get("Grant Amount", "")),
                str(row.get("Grant Term Start", "")),
            ]
            return f"R-{text_hash('|'.join(parts))}"

        df[DatasetFields.id_] = df.apply(_make_id, axis=1)

        # If still duplicated, append index suffix
        dupes = df[DatasetFields.id_].duplicated(keep=False)
        if dupes.any():
            df.loc[dupes, DatasetFields.id_] = [
                f"{v}-{i}" for i, v in enumerate(df.loc[dupes, DatasetFields.id_])
            ]

        # Extract year from Grant Term Start
        if "Grant Term Start" in df.columns:
            df[DatasetFields.year] = df["Grant Term Start"].apply(
                lambda x: int(str(x)[:4]) if pd.notna(x) else None
            )
            df[DatasetFields.start] = df["Grant Term Start"].apply(
                lambda x: str(x) if pd.notna(x) else None
            )

        if "Grant Term End" in df.columns:
            df[DatasetFields.end] = df["Grant Term End"].apply(
                lambda x: str(x) if pd.notna(x) else None
            )

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "Rockefeller"

        # Rename columns
        df = df.rename(
            columns={
                "Title": DatasetFields.institution,
                "Initiative": DatasetFields.program,
                "Grant Amount": DatasetFields.amount,
                "Description": DatasetFields.title,
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
        Get data from the Rockefeller Foundation.

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
            All grants from the Rockefeller Foundation for the specified
            time period and query, formatted into award_pynder standard format.
        """
        try:
            # Build URL with query and date params
            params: dict[str, str] = {
                "post_type": "grant",
                "download": "filter",
            }
            if query:
                params["keyword"] = query
            if from_datetime:
                from_dt = DataSource._parse_datetime(from_datetime)
                params["from_month"] = f"{from_dt.month:02d}"
                params["from_year"] = str(from_dt.year)
            if to_datetime:
                to_dt = DataSource._parse_datetime(to_datetime)
                params["to_month"] = f"{to_dt.month:02d}"
                params["to_year"] = str(to_dt.year)

            resp = requests.get(_ROCKEFELLER_URL, params=params, timeout=300)
            resp.raise_for_status()

            # The response should be CSV data
            content_type = resp.headers.get("content-type", "")
            if "text/csv" in content_type or "application/csv" in content_type:
                df = pd.read_csv(StringIO(resp.text))
            else:
                # Try parsing as CSV anyway
                try:
                    df = pd.read_csv(StringIO(resp.text))
                except Exception:
                    log.warning("Rockefeller did not return CSV data")
                    return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            if df.empty:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            return Rockefeller._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching Rockefeller data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
