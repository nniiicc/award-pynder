#!/usr/bin/env python

from __future__ import annotations

import logging
import time
from copy import deepcopy
from datetime import datetime

import pandas as pd
import requests

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
_DEFAULT_CHUNK_SIZE = 50
_MAX_PAGES = 200

_DEFAULT_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Description",
    "Start Date",
    "End Date",
    "Award Amount",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Funding Agency",
    "Funding Sub Agency",
]

_DEFAULT_AGENCIES = [
    {"name": "Department of Agriculture", "tier": "toptier", "type": "awarding"},
    {"name": "Department of Defense", "tier": "toptier", "type": "awarding"},
    {
        "name": "National Aeronautics and Space Administration",
        "tier": "toptier",
        "type": "awarding",
    },
    {
        "name": "Environmental Protection Agency",
        "tier": "toptier",
        "type": "awarding",
    },
    {"name": "Department of Education", "tier": "toptier", "type": "awarding"},
    {
        "name": "Institute of Museum and Library Services",
        "tier": "toptier",
        "type": "awarding",
    },
    {"name": "Smithsonian Institution", "tier": "toptier", "type": "awarding"},
    {"name": "Department of Commerce", "tier": "toptier", "type": "awarding"},
    {
        "name": "Department of the Interior",
        "tier": "toptier",
        "type": "awarding",
    },
]

_DEFAULT_PAYLOAD: dict = {
    "fields": _DEFAULT_FIELDS,
    "filters": {
        "agencies": _DEFAULT_AGENCIES,
        "award_type_codes": ["02", "03", "04", "05"],
        "keywords": [],
        "recipient_type_names": ["higher_education"],
        "time_period": [],
    },
    "limit": _DEFAULT_CHUNK_SIZE,
    "page": 1,
    "order": "desc",
    "subawards": False,
}

###############################################################################


class USASpending(DataSource):
    """Data source for USASpending.gov."""

    @staticmethod
    def _format_payload(
        keywords: list[str],
        from_datetime: str | datetime | None,
        to_datetime: str | datetime | None,
        page: int = 1,
    ) -> dict:
        payload = deepcopy(_DEFAULT_PAYLOAD)
        payload["filters"]["keywords"] = keywords
        payload["page"] = page

        if from_datetime and to_datetime:
            from_dt = DataSource._parse_datetime(from_datetime)
            to_dt = DataSource._parse_datetime(to_datetime)
            payload["filters"]["time_period"] = [
                {
                    "start_date": from_dt.date().isoformat(),
                    "end_date": to_dt.date().isoformat(),
                }
            ]

        return payload

    @staticmethod
    def _fetch_all_pages(
        payload: dict,
        raise_on_error: bool = True,
    ) -> pd.DataFrame:
        """Fetch all pages for a given payload."""
        all_results: list[dict] = []
        page = 1

        while page <= _MAX_PAGES:
            payload["page"] = page
            retries = 0
            max_retries = 5
            while retries <= max_retries:
                try:
                    resp = requests.post(
                        _USASPENDING_API_URL,
                        json=payload,
                        timeout=300,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    results = data.get("results", [])
                    all_results.extend(results)
                    break

                except requests.exceptions.HTTPError as e:
                    if resp.status_code == 503 and retries < max_retries:
                        retries += 1
                        wait = 5 * retries
                        log.warning(
                            f"USASpending 503 on page {page}, "
                            f"retry {retries}/{max_retries} in {wait}s"
                        )
                        time.sleep(wait)
                        continue
                    if raise_on_error:
                        raise
                    log.error(f"Error fetching USASpending page {page}: {e}")
                    return pd.DataFrame(columns=_DEFAULT_FIELDS)

                except Exception as e:
                    if raise_on_error:
                        raise
                    log.error(f"Error fetching USASpending page {page}: {e}")
                    return pd.DataFrame(columns=_DEFAULT_FIELDS)

            if not data.get("page_metadata", {}).get("hasNext", False):
                break

            page += 1
            time.sleep(1)

        if not all_results:
            return pd.DataFrame(columns=_DEFAULT_FIELDS)

        return pd.DataFrame(all_results)

    @staticmethod
    def _merge_multi_agency_awards(df: pd.DataFrame) -> pd.DataFrame:
        """Merge awards funded by multiple sub-agencies under the same ID."""
        if df.empty:
            return df

        def _join_unique(x: pd.Series) -> str:
            return "; ".join(sorted({str(v) for v in x if pd.notna(v)}))

        # Group by Award ID and aggregate
        grouped = df.groupby("Award ID", as_index=False).agg(
            {
                "Recipient Name": "first",
                "Description": "first",
                "Start Date": "min",
                "End Date": "max",
                "Award Amount": "sum",
                "Awarding Agency": _join_unique,
                "Awarding Sub Agency": _join_unique,
                "Funding Agency": _join_unique,
                "Funding Sub Agency": _join_unique,
            }
        )
        return grouped

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        if df.empty:
            result = pd.DataFrame(columns=ALL_DATASET_FIELDS)
            return result

        # Extract year from start date
        df[DatasetFields.year] = df["Start Date"].apply(
            lambda x: int(x[:4]) if pd.notna(x) and isinstance(x, str) else None
        )

        # Format dates
        df[DatasetFields.start] = df["Start Date"]
        df[DatasetFields.end] = df["End Date"]

        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "USASpending"

        # Rename columns
        df = df.rename(
            columns={
                "Recipient Name": DatasetFields.institution,
                "Award Amount": DatasetFields.amount,
                "Award ID": DatasetFields.id_,
                "Description": DatasetFields.title,
                "Awarding Agency": DatasetFields.program,
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
        Get data from USASpending.gov.

        Parameters
        ----------
        query : str, optional
            The query string to search for.
        from_datetime : str or datetime, optional
            The start date for the search. Data only available from 2007-10-01.
        to_datetime : str or datetime, optional
            The end date for the search.
        raise_on_error : bool, optional
            Whether to raise an error if the request fails.
        tqdm_kwargs : dict, optional
            Keyword arguments to pass to tqdm.

        Returns
        -------
        pd.DataFrame
            All grants from USASpending.gov for the specified time period and
            query, formatted into award_pynder standard format.
        """
        if from_datetime:
            from_dt = DataSource._parse_datetime(from_datetime)
            if from_dt.year < 2007 or (from_dt.year == 2007 and from_dt.month < 10):
                log.warning(
                    "USASpending data only available from 2007-10-01. "
                    "Results may be incomplete."
                )

        keywords = [query] if query else []

        # Stage 1: Search by keyword
        payload = USASpending._format_payload(
            keywords=keywords,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
        )

        awards = USASpending._fetch_all_pages(payload, raise_on_error=raise_on_error)

        if awards.empty:
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)

        # Stage 2: Re-query by Award ID to find multi-agency funding
        # Batch IDs to avoid 503 from oversized payloads
        award_ids = awards["Award ID"].unique().tolist()
        id_batch_size = 100
        id_results: list[pd.DataFrame] = []

        for i in range(0, len(award_ids), id_batch_size):
            batch = award_ids[i : i + id_batch_size]
            id_payload = deepcopy(_DEFAULT_PAYLOAD)
            id_payload["filters"] = {
                "agencies": _DEFAULT_AGENCIES,
                "award_type_codes": ["02", "03", "04", "05"],
                "recipient_type_names": ["higher_education"],
                "award_ids": batch,
            }
            batch_result = USASpending._fetch_all_pages(
                id_payload, raise_on_error=raise_on_error
            )
            if not batch_result.empty:
                id_results.append(batch_result)

        all_id_awards = (
            pd.concat(id_results, ignore_index=True)
            if id_results
            else pd.DataFrame(columns=_DEFAULT_FIELDS)
        )

        # Combine and deduplicate
        combined = pd.concat(
            [awards, all_id_awards], ignore_index=True
        ).drop_duplicates()

        # Merge multi-agency awards
        merged = USASpending._merge_multi_agency_awards(combined)

        return USASpending._format_dataframe(merged, query=query)
