.PHONY: install test lint format

install:
	uv sync --all-extras

test:
	uv run --no-sync --all-extras coverage run -m pytest src tests
	uv run --no-sync coverage combine
	uv run --no-sync coverage report
	uv run --no-sync coverage xml

lint:
	uv run --no-sync ruff check src tests examples || exit 1
	uv run --no-sync --all-extras mypy src tests examples || exit 1
	uv run --no-sync ruff format --check src tests examples || exit 1

format:
	uv run --no-sync ruff check src tests examples --fix
	uv run --no-sync ruff format src tests examples

readme-image:
	FORCE_COLOR=true uv run --no-sync python readme.py --help | ansitoimg --title '' docs/source/_static/example.svg
