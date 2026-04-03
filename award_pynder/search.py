"""Unified search across multiple award/grant data sources."""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime

import pandas as pd

from .sources import SOURCE_REGISTRY
from .sources.base import ALL_DATASET_FIELDS, DatasetFields

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


def _load_keywords(keywords: str | list[str]) -> list[str]:
    """Load keywords from a string, list, or file path.

    Parameters
    ----------
    keywords : str or list[str]
        A keyword string, list of keywords, or path to a CSV/text file
        containing one keyword per line.

    Returns
    -------
    list[str]
        List of keyword strings.
    """
    if isinstance(keywords, list):
        return keywords

    # Check if it's a file path
    if os.path.isfile(keywords):
        result = []
        with open(keywords) as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    result.append(row[0].strip())
        return [kw for kw in result if kw]

    return [keywords]


def _merge_queries(x: pd.Series) -> str:
    """Merge multiple query values with semicolon separator."""
    return "; ".join(sorted({str(v) for v in x if pd.notna(v)}))


def _resolve_sources(sources: list[str] | None) -> list[str]:
    """Resolve and validate source names against the registry."""
    if sources is None:
        return list(SOURCE_REGISTRY.keys())

    valid = []
    for s in sources:
        s_lower = s.lower()
        if s_lower not in SOURCE_REGISTRY:
            log.warning(f"Unknown source '{s}', skipping")
        else:
            valid.append(s_lower)
    return valid


def _collect_results(
    source_names: list[str],
    keyword_list: list[str],
    from_date: str | datetime,
    to_date: str | datetime,
    verbose: bool,
) -> list[pd.DataFrame]:
    """Query each source for each keyword, collecting results."""
    results: list[pd.DataFrame] = []
    tqdm_kwargs = {"leave": False, "disable": not verbose}

    for source_name in source_names:
        source_cls = SOURCE_REGISTRY[source_name]
        for keyword in keyword_list:
            try:
                if verbose:
                    log.info(f"Searching {source_name} for '{keyword}'...")
                df = source_cls.get_data(
                    query=keyword,
                    from_datetime=from_date,
                    to_datetime=to_date,
                    raise_on_error=False,
                    tqdm_kwargs=tqdm_kwargs,
                )
                if df is not None and not df.empty:
                    results.append(df)
            except Exception as e:
                log.warning(f"Error searching {source_name} for '{keyword}': {e}")
    return results


def _deduplicate(combined: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate results by (source, id), merging query strings."""
    if combined.empty or DatasetFields.id_ not in combined.columns:
        return combined[ALL_DATASET_FIELDS]

    group_keys = [DatasetFields.source, DatasetFields.id_]
    agg_dict = {
        col: (_merge_queries if col == DatasetFields.query else "first")
        for col in ALL_DATASET_FIELDS
        if col not in group_keys
    }
    grouped = combined.groupby(group_keys, as_index=False).agg(agg_dict)
    return grouped[ALL_DATASET_FIELDS]


def search_awards(
    keywords: str | list[str],
    sources: list[str] | None = None,
    from_date: str | datetime = "2019-01-01",
    to_date: str | datetime | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Search for awards across multiple funding databases.

    This is the main entry point for the award_pynder package, porting
    the ``search_awards()`` function from the R package awardFindR.

    Parameters
    ----------
    keywords : str or list[str]
        Search terms. Can be a single string, a list of strings, or a
        file path to a CSV/text file with one keyword per line.
    sources : list[str], optional
        List of source names to search. Defaults to all registered sources.
        Available sources: {source_list}
    from_date : str or datetime
        Start date for the search. Defaults to "2019-01-01".
    to_date : str or datetime, optional
        End date for the search. Defaults to today.
    verbose : bool
        Whether to show progress bars and status messages.

    Returns
    -------
    pd.DataFrame
        Combined results from all sources with standardized columns:
        {fields}. Results are deduplicated by (source, id), with
        keywords merged using "; " separator.
    """.format(
        source_list=", ".join(sorted(SOURCE_REGISTRY.keys())),
        fields=", ".join(ALL_DATASET_FIELDS),
    )
    keyword_list = _load_keywords(keywords)
    if not keyword_list:
        log.warning("No keywords provided")
        return pd.DataFrame(columns=ALL_DATASET_FIELDS)

    source_names = _resolve_sources(sources)
    if not source_names:
        log.warning("No valid sources specified")
        return pd.DataFrame(columns=ALL_DATASET_FIELDS)

    if to_date is None:
        to_date = datetime.now().date().isoformat()

    all_results = _collect_results(
        source_names, keyword_list, from_date, to_date, verbose
    )

    if not all_results:
        return pd.DataFrame(columns=ALL_DATASET_FIELDS)

    combined = pd.concat(all_results, ignore_index=True)
    return _deduplicate(combined)
