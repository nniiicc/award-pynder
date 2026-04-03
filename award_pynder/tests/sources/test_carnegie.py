#!/usr/bin/env python

from award_pynder.sources.carnegie import Carnegie

from ..utils import assert_dataset_basics

###############################################################################


def test_carnegie() -> None:
    # Get data with narrow date range
    df = Carnegie.get_data(
        query="education",
        from_datetime="2022-01-01",
        to_datetime="2023-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
