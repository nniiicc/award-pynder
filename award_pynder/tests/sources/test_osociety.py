#!/usr/bin/env python

from award_pynder.sources.osociety import OpenSociety

from ..utils import assert_dataset_basics

###############################################################################


def test_osociety() -> None:
    # Get data with narrow date range
    df = OpenSociety.get_data(
        query="education",
        from_datetime="2019-01-01",
        to_datetime="2020-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
