# Contributing to Award Pynder

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/si2-urssi/award-pynder.git
cd award-pynder

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
uv sync --extra dev --extra test --extra lint

# Verify installation
uv run award-pynder --help
```

## Code Style

- **Formatter/Linter:** [Ruff](https://docs.astral.sh/ruff/) (line length 88)
- **Type checking:** mypy
- PEP 8 with 88-character line length
- Type hints on all function signatures
- Docstrings on all public functions (Args/Returns/Raises format)

```bash
# Lint
uvx ruff check award_pynder/

# Format
uvx ruff format award_pynder/

# Or use pre-commit
pre-commit run --all-files
```

## Running Tests

Tests make real HTTP requests to external APIs. Use narrow date ranges to minimize load.

```bash
# Run all tests
uv run pytest -v

# Run a single source test
uv run pytest award_pynder/tests/sources/test_nsf.py -v

# Run the unified search tests
uv run pytest award_pynder/tests/test_search.py -v
```

## Adding a New Funding Source

1. Create `award_pynder/sources/<name>.py` with a class extending `DataSource`
2. Implement `get_data()` and `_format_dataframe()` — output must contain exactly the 12 standard fields from `ALL_DATASET_FIELDS`
3. Add the source to `SOURCE_REGISTRY` in `award_pynder/sources/__init__.py`
4. Add a test in `award_pynder/tests/sources/test_<name>.py` using `assert_dataset_basics()` from `award_pynder/tests/utils.py`
5. Update the source table in `README.md`

## Pull Requests

- Create a branch from `main`
- Ensure all tests pass and lint is clean
- Include a clear description of the change
- Link any related issues
