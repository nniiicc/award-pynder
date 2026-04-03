#!/usr/bin/env python

from __future__ import annotations

import logging
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .base import ALL_DATASET_FIELDS, DatasetFields, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_CARNEGIE_BASE_URL = "https://www.carnegie.org/grants/grants-database/"

###############################################################################


class Carnegie(DataSource):
    """Data source for the Carnegie Corporation of New York."""

    @staticmethod
    def _format_dataframe(
        df: pd.DataFrame,
        query: str | None = None,
    ) -> pd.DataFrame:
        # Add query and source
        df[DatasetFields.query] = query
        df[DatasetFields.source] = "Carnegie"

        # Rename columns
        df = df.rename(
            columns={
                "grantee": DatasetFields.institution,
                "amount": DatasetFields.amount,
                "program": DatasetFields.program,
                "grant_id": DatasetFields.id_,
                "title": DatasetFields.title,
                "abstract": DatasetFields.abstract,
                "year": DatasetFields.year,
            }
        )

        # Add missing columns
        for field in ALL_DATASET_FIELDS:
            if field not in df.columns:
                df[field] = None

        return df[ALL_DATASET_FIELDS]

    @staticmethod
    def _parse_award_row(
        row: BeautifulSoup,
        session: requests.Session,
        cookie: str | None,
    ) -> dict | None:
        """Parse a single award table row and fetch detail page."""
        cells = row.find_all("td")
        if len(cells) < 4:
            return None

        cell_texts = [c.get_text(strip=True) for c in cells]
        year = cell_texts[0]
        grantee = cell_texts[1]
        amount_str = cell_texts[2]
        program = cell_texts[3]

        # Clean amount
        amount = None
        if amount_str:
            cleaned = re.sub(r"[$,]", "", amount_str)
            try:
                amount = int(cleaned)
            except ValueError:
                amount = None

        # Extract grant ID from row
        row_id = row.get("id", "")
        grant_id = re.sub(r"^grant-", "", row_id) if row_id else None

        # Fetch detail page for title and abstract
        title = None
        abstract = None
        if grant_id:
            try:
                detail_url = f"{_CARNEGIE_BASE_URL}grant/{grant_id}/"
                headers = {
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": _CARNEGIE_BASE_URL,
                }
                if cookie:
                    headers["X-CSRFToken"] = cookie

                resp = session.get(detail_url, headers=headers, timeout=60)
                if resp.ok:
                    # Try JSON response first
                    try:
                        data = resp.json()
                        html_content = data.get("result", [""])[0]
                        detail_soup = BeautifulSoup(html_content, "html.parser")
                    except (ValueError, KeyError):
                        detail_soup = BeautifulSoup(resp.text, "html.parser")

                    # Extract from label/value pairs
                    labels = detail_soup.find_all("label", class_="grant-detail--label")
                    values = detail_soup.find_all("div", class_="grant-detail--text")
                    details = {
                        lbl.get_text(strip=True): val.get_text(strip=True)
                        for lbl, val in zip(labels, values, strict=False)
                    }
                    title = details.get("Project Title")
                    abstract = details.get("Description")

                time.sleep(1)
            except Exception as e:
                log.debug(f"Error fetching Carnegie detail for {grant_id}: {e}")

        return {
            "year": year,
            "grantee": grantee,
            "amount": amount,
            "program": program,
            "grant_id": grant_id or f"carnegie-{grantee}-{year}",
            "title": title,
            "abstract": abstract,
        }

    @staticmethod
    def get_data(  # noqa: C901
        query: str | None = None,
        from_datetime: str | datetime | None = None,
        to_datetime: str | datetime | None = None,
        raise_on_error: bool = True,
        tqdm_kwargs: dict | None = None,
    ) -> pd.DataFrame:
        """
        Get data from the Carnegie Corporation of New York.

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
            All grants from Carnegie Corporation for the specified time
            period and query, formatted into award_pynder standard format.
        """
        try:
            session = requests.Session()

            # Build URL with query and year params
            url = f"{_CARNEGIE_BASE_URL}?per_page=100"
            if query:
                url += f"&q={query}"
            if from_datetime and to_datetime:
                from_year = DataSource._parse_datetime(from_datetime).year
                to_year = DataSource._parse_datetime(to_datetime).year
                for y in range(from_year, to_year + 1):
                    url += f"&y={y}"

            # Initial request to get CSRF cookie
            resp = session.get(url, timeout=300)
            resp.raise_for_status()

            cookie = None
            for c in session.cookies:
                if "csrf" in c.name.lower():
                    cookie = c.value
                    break

            all_awards: list[dict] = []
            page = 1
            more_pages = True

            while more_pages:
                page_url = f"{url}&page={page}"
                resp = session.get(page_url, timeout=300)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("tbody > tr")

                if not rows:
                    break

                for row in tqdm(
                    rows,
                    desc=f"Fetching Carnegie page {page}",
                    **(tqdm_kwargs or {}),
                ):
                    award = Carnegie._parse_award_row(row, session, cookie)
                    if award:
                        all_awards.append(award)

                # Check for next page
                next_link = soup.find(string=re.compile(r"Next"))
                more_pages = next_link is not None
                page += 1

            if not all_awards:
                return pd.DataFrame(columns=ALL_DATASET_FIELDS)

            df = pd.DataFrame(all_awards)
            return Carnegie._format_dataframe(df, query=query)

        except Exception as e:
            if raise_on_error:
                raise
            log.error(
                f"Error while fetching Carnegie data: {e}; "
                f"'raise_on_error' is False, ignoring..."
            )
            return pd.DataFrame(columns=ALL_DATASET_FIELDS)
