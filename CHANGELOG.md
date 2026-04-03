# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unified `search_awards()` function for querying multiple sources at once
- CLI entry point (`award-pynder`) with click
- 11 new funding sources: USASpending, Gates Foundation, RWJF, Arnold Ventures, SSRC, Carnegie Corporation, Rockefeller Foundation, Open Society Foundations, MacArthur Foundation, Open Philanthropy (stub), Russell Sage Foundation (stub)
- Source registry (`SOURCE_REGISTRY`) for dynamic source dispatch
- Shared Algolia search helper for Arnold and SSRC sources
- Shared HTTP and text-hash utilities
- Keyword loading from CSV files
- Result deduplication across sources

### Fixed
- Templeton Foundation: unreachable date-filtering code moved inside try block
- Templeton Foundation: added missing `tqdm_kwargs` parameter

### Changed
- Updated CI workflow to use uv and Python version matrix (3.11, 3.12, 3.13)

## [0.1.0] - Initial Development

### Added
- NSF source (REST JSON API)
- NIH source (REST JSON API)
- Mellon Foundation source (GraphQL API)
- Sloan Foundation source (HTML scraping)
- Templeton Foundation source (HTML scraping)
- Standardized 12-field output schema
- Test utilities with `assert_dataset_basics()`
