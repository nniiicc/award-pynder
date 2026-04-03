"""Data sources package for award_pynder."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import DataSource

from .arnold import Arnold
from .carnegie import Carnegie
from .gates import Gates
from .macarthur import MacArthur
from .mellon import Mellon
from .nih import NIH
from .nsf import NSF
from .ophil import OpenPhilanthropy
from .osociety import OpenSociety
from .rockefeller import Rockefeller
from .rsf import RSF
from .rwjf import RWJF
from .sloan import Sloan
from .ssrc import SSRC
from .templeton import Templeton
from .usaspending import USASpending

SOURCE_REGISTRY: dict[str, type[DataSource]] = {
    "nsf": NSF,
    "nih": NIH,
    "mellon": Mellon,
    "sloan": Sloan,
    "templeton": Templeton,
    "usaspending": USASpending,
    "gates": Gates,
    "rwjf": RWJF,
    "arnold": Arnold,
    "ssrc": SSRC,
    "carnegie": Carnegie,
    "rockefeller": Rockefeller,
    "osociety": OpenSociety,
    "macarthur": MacArthur,
    "ophil": OpenPhilanthropy,
    "rsf": RSF,
}
