#!/usr/bin/env python

from award_pynder.sources.macarthur import MacArthur

from ..utils import assert_dataset_basics

###############################################################################


def test_macarthur() -> None:
    # Get data with narrow date range
    df = MacArthur.get_data(
        query="climate",
        from_datetime="2018-01-01",
        to_datetime="2020-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
