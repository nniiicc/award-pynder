#!/usr/bin/env python

from award_pynder.sources.usaspending import USASpending

from ..utils import assert_dataset_basics

###############################################################################


def test_usaspending() -> None:
    # Get data with narrow date range
    df = USASpending.get_data(
        query="climate",
        from_datetime="2023-01-01",
        to_datetime="2023-03-01",
    )

    # Run tests
    assert_dataset_basics(df)
