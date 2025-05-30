.PHONY: install test lint lint-typos lint-examples format

install:
	uv sync --all-extras

test:
	uv run --no-sync --all-extras coverage run -m pytest src tests
	uv run --no-sync coverage combine
	uv run --no-sync coverage report
	uv run --no-sync coverage xml

lint:
	uv run --no-sync ruff check src tests examples || exit 1
	uv run --no-sync --all-extras mypy src tests || exit 1
	uv run --no-sync --all-extras pyright src tests || exit 1
	uv run --no-sync ruff format --check src tests || exit 1

lint-examples:
	uv run --directory examples/defer_import_slow_startup --all-extras mypy -p defer_import || exit 1
	uv run --directory examples/defer_import_slow_startup --all-extras pyright defer_import || exit 1
	uv run --directory examples/defer_import_slow_startup --all-extras basedpyright defer_import || exit 1

lint-typos:
	typos

format:
	uv run --no-sync ruff check src tests examples --fix
	uv run --no-sync ruff format src tests examples

readme-image:
	FORCE_COLOR=true uv run --no-sync python readme.py --help | ansitoimg --title '' --width 80 docs/source/_static/example.svg
