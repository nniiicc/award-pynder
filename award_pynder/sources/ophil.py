#!/usr/bin/env python

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from .base import ALL_DATASET_FIELDS, DataSource

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class OpenPhilanthropy(DataSource):
    """Data source for Open Philanthropy.

    Notes
    -----
    This source is currently unavailable. The Open Philanthropy website
    uses Cloudflare bot protection that blocks automated requests.
    This stub is included for registry completeness and will be
    implemented once an accessible API endpoint is identified.
    """

    @staticmethod
    def _format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError(
            "Open Philanthropy source is not yet implemented. "
            "The website blocks automated requests."
        )

    @staticmethod
    def get_data(
        query: str | None = None,
        from_datetime: str | datetime | None = None,
        to_datetime: str | datetime | None = None,
        raise_on_error: bool = True,
        tqdm_kwargs: dict | None = None,
    ) -> pd.DataFrame:
        """
        Get data from Open Philanthropy.

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
            Empty DataFrame. This source is not yet implemented.
        """
        log.warning(
            "Open Philanthropy source is not yet available. "
            "The website blocks automated requests (Cloudflare 403)."
        )
        return pd.DataFrame(columns=ALL_DATASET_FIELDS)
