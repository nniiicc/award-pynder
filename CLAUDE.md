# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Award Pynder searches for grant/award data across multiple funding agency databases and websites. It is a Python port of the R package [awardFindR](https://github.com/ropensci/awardFindR).

## Commands

```bash
# Install (editable, all extras)
uv sync
# or: pip install -e ".[dev,lint,test]"

# Run all tests (tests hit live APIs — expect slow runs and rate-limit pauses)
uv run pytest

# Run a single test
uv run pytest award_pynder/tests/sources/test_nsf.py -v

# Lint and format
uvx ruff check award_pynder/
uvx ruff format award_pynder/
# or via pre-commit: pre-commit run --all-files

# CLI
uv run award-pynder "keyword" --sources nsf,nih --from-date 2020-01-01

# Task runner
just              # list all commands
just test
just lint
just clean
```

## Architecture

All funding sources follow the same pattern defined in `award_pynder/sources/base.py`:

- **`DataSource`** — abstract base class. Each source implements `get_data()` (public entry point) and `_format_dataframe()` (normalizes source-specific columns to a standard schema).
- **`DatasetFields`** / **`ALL_DATASET_FIELDS`** — canonical column names every source must output: `institution`, `pi`, `year`, `start`, `end`, `program`, `amount`, `id`, `title`, `abstract`, `query`, `source`.
- **`SOURCE_REGISTRY`** in `award_pynder/sources/__init__.py` — maps short names to source classes, used by `search_awards()` for dynamic dispatch.
- **`search_awards()`** in `award_pynder/search.py` — unified entry point that queries multiple sources by keyword, deduplicates results.
- **CLI** in `award_pynder/bin/cli.py` — click-based CLI entry point (`award-pynder` command).

### Sources (`award_pynder/sources/`)

| Class | File | API style | Status |
|-------|------|-----------|--------|
| `NSF` | `nsf.py` | REST JSON (api.nsf.gov) | Working |
| `NIH` | `nih.py` | REST JSON (NIH Reporter v2) | Working |
| `Mellon` | `mellon.py` | GraphQL (mellon.org) | Working |
| `Sloan` | `sloan.py` | HTML scraping (sloan.org) | Working |
| `Templeton` | `templeton.py` | HTML scraping (templeton.org) | Working |
| `USASpending` | `usaspending.py` | REST JSON (api.usaspending.gov) | Working |
| `Gates` | `gates.py` | REST JSON (gatesfoundation.org) | Endpoint may have changed |
| `RWJF` | `rwjf.py` | REST JSON (rwjf.org) | Endpoint may have changed |
| `Arnold` | `arnold.py` | Algolia search (via `_algolia.py`) | API key may need refresh |
| `SSRC` | `ssrc.py` | Algolia search (via `_algolia.py`) | API key may need refresh |
| `Carnegie` | `carnegie.py` | HTML scraping + CSRF (carnegie.org) | Working |
| `Rockefeller` | `rockefeller.py` | CSV download (rockefellerfoundation.org) | Working |
| `OpenSociety` | `osociety.py` | HTML scraping (opensocietyfoundations.org) | Selectors may need update |
| `MacArthur` | `macarthur.py` | Solr JSON (CrownPeak) | Endpoint may have moved |
| `OpenPhilanthropy` | `ophil.py` | Stub — Cloudflare blocks requests | Not implemented |
| `RSF` | `rsf.py` | Stub — search endpoint restructured | Not implemented |

### Shared helpers

- `award_pynder/utils.py` — `http_request()` (shared HTTP with timeout), `text_hash()` (deterministic ID generation)
- `award_pynder/sources/_algolia.py` — shared Algolia search helper used by Arnold and SSRC

### Adding a new source

1. Create `award_pynder/sources/<name>.py` with a class extending `DataSource`.
2. Implement `get_data()` and `_format_dataframe()`. Output must contain exactly `ALL_DATASET_FIELDS`.
3. Add the source to `SOURCE_REGISTRY` in `award_pynder/sources/__init__.py`.
4. Add a test in `award_pynder/tests/sources/test_<name>.py` that calls `get_data()` with a narrow date range and passes through `assert_dataset_basics()` from `award_pynder/tests/utils.py`.

## Testing notes

- Tests live in `award_pynder/tests/` (inside the package, not a top-level `tests/` dir).
- All tests make real HTTP requests to external APIs — no mocking. They use narrow date ranges to keep response sizes small.
- `assert_dataset_basics()` validates column schema, no duplicates, and non-empty results.

## Build system

- Uses `setuptools` + `setuptools_scm` (versions derived from git tags), **not** hatchling.
- All config in `pyproject.toml`. Ruff for linting/formatting.
- CLI entry point: `award-pynder` (defined in `[project.scripts]`).
- Dependencies: beautifulsoup4, click, lxml, pandas, python-dateutil, requests, tqdm.
