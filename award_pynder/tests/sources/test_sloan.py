#!/usr/bin/env python

from award_pynder.sources.sloan import Sloan

from ..utils import assert_dataset_basics

###############################################################################


def test_sloan() -> None:
    # Get data — Sloan does client-side date filtering, so use a wide range
    df = Sloan.get_data(
        query="software",
        from_datetime="2024-01-01",
        to_datetime="2026-12-31",
        tqdm_kwargs={"leave": False},
    )

    # Run tests
    assert_dataset_basics(df)
