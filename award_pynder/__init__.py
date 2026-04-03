"""Top-level package for award_pynder."""

from importlib.metadata import PackageNotFoundError, version

from .search import search_awards
from .sources import SOURCE_REGISTRY

try:
    __version__ = version("award-pynder")
except PackageNotFoundError:
    __version__ = "uninstalled"

__author__ = "Eva Maxfield Brown"
__email__ = "evamxb@uw.edu"

__all__ = ["SOURCE_REGISTRY", "__version__", "search_awards"]
