#!/usr/bin/env python

from award_pynder.sources.rockefeller import Rockefeller

from ..utils import assert_dataset_basics

###############################################################################


def test_rockefeller() -> None:
    # Get data with narrow date range
    df = Rockefeller.get_data(
        query="health",
        from_datetime="2020-01-01",
        to_datetime="2021-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
