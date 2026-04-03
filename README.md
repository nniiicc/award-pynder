# Award Pynder

[![CI](https://github.com/nniiicc/award-pynder/actions/workflows/ci.yml/badge.svg)](https://github.com/nniiicc/award-pynder/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/award-pynder.svg)](https://pypi.org/project/award-pynder/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

Search for awards and grants across multiple funding databases and websites.

Updated Python port of the original [awardFindR](https://github.com/ropensci/awardFindR) R package.

## Installation

```bash
pip install award-pynder
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add award-pynder
```

## Quick Start

### Python API

```python
from award_pynder import search_awards

# Search across all sources
results = search_awards(
    keywords="climate change",
    from_date="2020-01-01",
    to_date="2023-01-01",
)

# Search specific sources
results = search_awards(
    keywords=["machine learning", "data science"],
    sources=["nsf", "nih"],
    from_date="2020-01-01",
)

# Load keywords from a file (one per line)
results = search_awards(keywords="keywords.csv", sources=["nsf"])
```

### Individual Sources

```python
from award_pynder.sources.nsf import NSF

df = NSF.get_data(
    query="climate",
    from_datetime="2020-01-01",
    to_datetime="2021-01-01",
)
```

### Command Line

```bash
# Search NSF and NIH for "climate change"
award-pynder "climate change" --sources nsf,nih --from-date 2020-01-01

# Save results to CSV
award-pynder "machine learning" -s nsf -o results.csv

# Verbose output with progress bars
award-pynder "data science" -s nsf,nih,mellon -v
```

## Supported Sources

| Source | Key | Status |
|--------|-----|--------|
| National Science Foundation | `nsf` | Working |
| National Institutes of Health | `nih` | Working |
| Andrew W. Mellon Foundation | `mellon` | Working |
| Alfred P. Sloan Foundation | `sloan` | Working |
| John Templeton Foundation | `templeton` | Working |
| USASpending.gov | `usaspending` | Working |
| Social Science Research Council | `ssrc` | Working |
| Carnegie Corporation of New York | `carnegie` | Working |
| Bill & Melinda Gates Foundation | `gates` | Working |
| Rockefeller Foundation | `rockefeller` | Working |
| Arnold Ventures | `arnold` | Working |
| MacArthur Foundation | `macarthur` | Working |
| Open Society Foundations | `osociety` | Working |
| Robert Wood Johnson Foundation | `rwjf` | Working |
| Open Philanthropy | `ophil` | Unavailable |
| Russell Sage Foundation | `rsf` | Unavailable |

**Working** — Verified and reliable. **Experimental** — Implemented but endpoint may have changed since original R package. **Unavailable** — Endpoint blocked or restructured; returns empty results.

## Output Schema

All sources normalize data to a common schema with these fields:

| Field | Description |
|-------|-------------|
| `institution` | Grantee organization |
| `pi` | Principal investigator |
| `year` | Award year |
| `start` | Project start date |
| `end` | Project end date |
| `program` | Funding program or agency |
| `amount` | Award amount |
| `id` | Unique grant identifier |
| `title` | Grant title |
| `abstract` | Grant abstract or description |
| `query` | Search keyword used |
| `source` | Data source name |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the Mozilla Public License 2.0 — see the [LICENSE](LICENSE) file for details.
