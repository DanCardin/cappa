.PHONY: install test lint format build publish

PACKAGE_VERSION = $(shell python -c 'import importlib.metadata; print(importlib.metadata.version("responsaas"))')

install:
	poetry install -E docstring

test:
	coverage run -m pytest src tests
	coverage combine
	coverage report
	coverage xml

lint:
	ruff check src tests || exit 1
	mypy src tests || exit 1
	ruff format --check src tests || exit 1

format:
	ruff check src tests --fix
	ruff format src tests

readme-image:
	FORCE_COLOR=true python readme.py --help | ansitoimg --title '' docs/source/_static/example.svg
	
