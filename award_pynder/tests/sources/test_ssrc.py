#!/usr/bin/env python

from award_pynder.sources.ssrc import SSRC

from ..utils import assert_dataset_basics

###############################################################################


def test_ssrc() -> None:
    # Get data with narrow date range
    df = SSRC.get_data(
        query="data",
        from_datetime="2022-01-01",
        to_datetime="2023-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
