#!/usr/bin/env python

from award_pynder.sources.arnold import Arnold

from ..utils import assert_dataset_basics

###############################################################################


def test_arnold() -> None:
    # Get data with narrow date range
    df = Arnold.get_data(
        query="education",
        from_datetime="2020-01-01",
        to_datetime="2021-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
