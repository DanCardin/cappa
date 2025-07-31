.PHONY: install-lowest install test lint lint-base lint-312 lint-typos lint-examples format

install-lowest:
	uv sync --all-extras --resolution lowest-direct

install:
	uv sync --all-extras --resolution highest

test:
	@PYTEST_ARGS="$$(uv run --frozen python -c 'import sys; print("--ignore=tests/py312" if sys.version_info < (3,12) else "")')"; \
	uv run --frozen coverage run -m pytest src tests "$$PYTEST_ARGS"

coverage:
	uv run --frozen coverage combine
	uv run --frozen coverage report
	uv run --frozen coverage xml

lint:
	uv run --frozen ruff check src tests examples || exit 1
	uv run --frozen --all-extras mypy src tests || exit 1
	uv run --frozen --all-extras pyright src tests || exit 1
	uv run --frozen ruff format --check src tests || exit 1

lint-examples:
	uv run --directory examples/defer_import_slow_startup --all-extras mypy -p defer_import || exit 1
	uv run --directory examples/defer_import_slow_startup --all-extras pyright defer_import || exit 1
	uv run --directory examples/defer_import_slow_startup --all-extras basedpyright defer_import || exit 1

lint-typos:
	typos

format:
	uv run --frozen ruff check src tests examples --fix
	uv run --frozen ruff format src tests examples

readme-image:
	FORCE_COLOR=true uv run --no-sync python readme.py --help | ansitoimg --title '' --width 80 docs/source/_static/example.svg
