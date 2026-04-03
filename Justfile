# list all available commands
default:
  just --list

###############################################################################
# Basic project and env management

# clean all build, python, and lint files
clean:
	rm -fr dist
	rm -fr .eggs
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	rm -fr .mypy_cache
	rm -fr .ruff_cache

# install with all deps
install:
    uv sync --extra dev --extra lint --extra test

# lint and format check
lint:
	uvx ruff check award_pynder/
	uvx ruff format --check award_pynder/

# run all tests
test:
	uv run pytest -v

# full package check (Python equivalent of R CMD check)
check:
	uv build
	uvx twine check dist/*
	uvx ruff check award_pynder/
	uvx ruff format --check award_pynder/
	uv run pytest -v

###############################################################################
# Release and versioning

# tag a new version
tag-for-release version:
	git tag -a "{{version}}" -m "{{version}}"
	echo "Tagged: $(git tag --sort=-version:refname| head -n 1)"

# release a new version
release:
	git push --follow-tags