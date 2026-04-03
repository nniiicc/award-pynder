# award-pynder Copilot Instructions

Python port of [awardFindR](https://github.com/ropensci/awardFindR) — searches grant award databases (NSF, NIH, Sloan, Mellon, Templeton) and returns standardized `pd.DataFrame` results.

## Build and Test

```bash
just install   # pip install -e ".[dev,lint,test]"
just lint      # pre-commit run --all-files (black → ruff --fix → mypy)
just test      # pytest
```

## Architecture

All funding sources live in `award_pynder/sources/` and inherit from `DataSource` ([sources/base.py](../award_pynder/sources/base.py)):

- All methods are `@staticmethod` — sources are never instantiated; call as `NSF.get_data(...)`
- Every `get_data()` returns a `pd.DataFrame` with **exactly** the columns in `ALL_DATASET_FIELDS` (from `base.py`): `institution`, `pi`, `year`, `start`, `end`, `program`, `amount`, `id`, `title`, `abstract`, `query`, `source`
- Missing fields are filled with `None`; column order is always enforced via `df[ALL_DATASET_FIELDS]`
- The `_format_dataframe()` static method maps source-specific fields to the standard schema

### Source-specific notes

| Source | API type | Pagination | Auth |
|--------|----------|------------|------|
| NSF | REST JSON | offset (chunk=25) | none |
| NIH | REST POST JSON | offset (chunk=500); raises `ValueError` if total ≥ 10,000 | none |
| Sloan | HTML scrape (BeautifulSoup) | page (chunk=3000) | none |
| Mellon | GraphQL | offset (chunk=100); N+1 per-grant amount query | none |
| Templeton | Two-stage HTML scrape + `pd.read_html` | single fetch (limit=500) | none |

## Code Style

- `from __future__ import annotations` at top of every source module
- Type hints required everywhere (`mypy: disallow_untyped_defs = true`)
- Docstrings required in source files (ruff `D` rules); suppressed in test files
- Line length: 88; formatter: black; linter: ruff (E, F, D, I001, UP, N, C, B, A001, RUF)

## Project Conventions

- **Chunked pagination pattern:** private `_get_chunk(...)` fetches one page; public `get_data(...)` loops with `tqdm` and collects chunks into a final `pd.concat`
- **Rate limiting:** `time.sleep(2)` after every HTTP request
- **Error handling:** `raise_on_error: bool = True` param on `get_data`; when `False`, `_get_chunk` logs and returns `None` instead of raising
- **`tqdm` integration:** `get_data` accepts `tqdm_kwargs: dict | None` passed through to `tqdm()`; tests pass `{"leave": False}`
- **Adding a new source:** subclass `DataSource`, implement `_format_dataframe` and `get_data` as `@staticmethod`, export from `sources/__init__.py`

## Tests

Tests in `award_pynder/tests/sources/` make **real live HTTP calls** — no mocking. Use narrow date ranges to limit results. Every test calls `assert_dataset_basics(df)` from [`tests/utils.py`](../award_pynder/tests/utils.py), which asserts: correct columns, no duplicate rows, unique IDs, non-empty result.
