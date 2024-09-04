.PHONY: install test lint format

PACKAGE_VERSION = $(shell python -c 'import importlib.metadata; print(importlib.metadata.version("responsaas"))')

install:
	uv sync --all-extras

test:
	uv run --all-extras coverage run -m pytest src tests
	uv run coverage combine
	uv run coverage report
	uv run coverage xml

lint:
	uv run ruff check src tests examples || exit 1
	uv run --all-extras mypy src tests examples || exit 1
	uv run ruff format --check src tests examples || exit 1

format:
	uv run ruff check src tests examples --fix
	uv run ruff format src tests examples

readme-image:
	FORCE_COLOR=true uv run python readme.py --help | ansitoimg --title '' docs/source/_static/example.svg
