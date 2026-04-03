#!/usr/bin/env python

from award_pynder.sources.gates import Gates

from ..utils import assert_dataset_basics

###############################################################################


def test_gates() -> None:
    # Get data with narrow date range
    df = Gates.get_data(
        query="education",
        from_datetime="2022-01-01",
        to_datetime="2023-01-01",
    )

    # Run tests
    assert_dataset_basics(df)
