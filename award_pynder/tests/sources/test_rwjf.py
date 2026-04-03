#!/usr/bin/env python

from award_pynder.sources.rwjf import RWJF

from ..utils import assert_dataset_basics

###############################################################################


def test_rwjf() -> None:
    # Get data with narrow date range
    df = RWJF.get_data(
        query="health",
        from_datetime="2022-01-01",
        to_datetime="2023-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
