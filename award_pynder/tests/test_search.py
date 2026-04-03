#!/usr/bin/env python

import os
import tempfile

import pandas as pd

from award_pynder.search import search_awards
from award_pynder.sources.base import ALL_DATASET_FIELDS

###############################################################################


def test_search_single_keyword_single_source() -> None:
    """Test basic search with one keyword and one source."""
    df = search_awards(
        keywords="climate",
        sources=["nsf"],
        from_date="2014-01-01",
        to_date="2014-02-01",
    )

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == set(ALL_DATASET_FIELDS)
    assert len(df) > 0
    assert (df["source"] == "NSF").all()


def test_search_keyword_list() -> None:
    """Test search with a list of keywords."""
    df = search_awards(
        keywords=["climate", "ocean"],
        sources=["nsf"],
        from_date="2014-01-01",
        to_date="2014-02-01",
    )

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == set(ALL_DATASET_FIELDS)
    assert len(df) > 0


def test_search_keyword_from_file() -> None:
    """Test loading keywords from a file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("climate\nocean\n")
        temp_path = f.name

    try:
        df = search_awards(
            keywords=temp_path,
            sources=["nsf"],
            from_date="2014-01-01",
            to_date="2014-02-01",
        )

        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == set(ALL_DATASET_FIELDS)
        assert len(df) > 0
    finally:
        os.unlink(temp_path)


def test_search_unknown_source_skipped() -> None:
    """Test that unknown sources are skipped gracefully."""
    df = search_awards(
        keywords="climate",
        sources=["nsf", "nonexistent_source"],
        from_date="2014-01-01",
        to_date="2014-02-01",
    )

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == set(ALL_DATASET_FIELDS)
    assert len(df) > 0


def test_search_empty_results() -> None:
    """Test that nonsense queries return empty DataFrame with correct schema."""
    df = search_awards(
        keywords="xyzzy_no_results_12345",
        sources=["nsf"],
        from_date="2014-01-01",
        to_date="2014-01-02",
    )

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == set(ALL_DATASET_FIELDS)
