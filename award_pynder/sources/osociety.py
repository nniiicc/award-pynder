#!/usr/bin/env python

from __future__ import annotations

import logging
import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_OSOCIETY_BASE_URL = "https://www.opensocietyfoundations.org/grants/past"

###############################################################################


class OpenSociety(DataSource):
    """Data source for the Open Society Foundations."""

    @staticmethod
    def _parse_entry(entry: BeautifulSoup) -> dict:  # noqa: C901
        """Parse a single grant entry from the HTML."""
        # Extract institution from h2
        h2 = entry.find("h2")
        institution = h2.get_text(strip=True) if h2 else None
        grant_id = entry.get("id")

        year = None
        amount = None
        program = None
        description = None

        # Look for labeled spans (original structure)
        labels = entry.find_all("span", class_=re.compile(r"label", re.IGNORECASE))
        values = entry.find_all("span", class_=re.compile(r"value", re.IGNORECASE))

        label_value_map = {}
        for lbl, val in zip(labels, values, strict=False):
            label_value_map[lbl.get_text(strip=True)] = val.get_text(strip=True)

        # Try year from value spans
        year_span = entry.find(
            "span",
            class_=re.compile(r"value(?!.*amount)", re.IGNORECASE),
        )
        if year_span:
            try:
                year = int(year_span.get_text(strip=True))
            except ValueError:
                pass

        # Amount
        amount_span = entry.find("span", class_=re.compile(r"amount", re.IGNORECASE))
        if amount_span:
            amount_text = re.sub(r"[$,]", "", amount_span.get_text(strip=True))
            try:
                amount = int(amount_text)
            except ValueError:
                pass

        # Look for program and description in text/paragraph elements
        for p in entry.find_all("p"):
            text = p.get_text(strip=True)
            if "Program" in (p.get("class") or [""]):
                program = text
            elif len(text) > 50:
                description = text

        # Check label-value pairs
        if "Referring Program" in label_value_map:
            program = label_value_map["Referring Program"]
        if "Description" in label_value_map:
            description = label_value_map["Description"]

        return {
            "institution": institution,
            "year": year,
            "grant_id": grant_id or f"osf-{institution}-{year}",
            "amount": amount,
            "program": program,
            "description": description,
        }

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "Open Society"

        # Rename columns
        df = df.rename(
            columns={
                "institution": DatasetFields.institution,
                "year": DatasetFields.year,
                "grant_id": DatasetFields.id_,
                "amount": DatasetFields.amount,
                "program": DatasetFields.program,
                "description": DatasetFields.title,
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
        Get data from the Open Society Foundations.

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
            All grants from Open Society Foundations for the specified time
            period and query, formatted into award_pynder standard format.
        """
        try:
            # Build URL with query and year params
            # Note: xhr=1 triggers Cloudflare bot protection, so we
            # fetch the full server-rendered HTML page instead
            params: dict[str, str] = {}
            if query:
                params["filter_keyword"] = query

            if from_datetime and to_datetime:
                from_year = DataSource._parse_datetime(from_datetime).year
                to_year = DataSource._parse_datetime(to_datetime).year
                years = ",".join(str(y) for y in range(from_year, to_year + 1))
                params["filter_year"] = years

            resp = requests.get(_OSOCIETY_BASE_URL, params=params, timeout=300)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try the R package's original selector first
            entries = soup.find_all("div", attrs={"data-grants-database-single": True})

            # If not found, try alternate selectors for redesigned site
            if not entries:
                entries = soup.find_all(
                    "div", class_=re.compile(r"grant", re.IGNORECASE)
                )

            if not entries:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            rows = [OpenSociety._parse_entry(entry) for entry in entries]

            if not rows:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            df = pd.DataFrame(rows)
            return OpenSociety._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching Open Society data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
