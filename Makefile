.PHONY: install test lint format build publish

PACKAGE_VERSION = $(shell python -c 'import importlib.metadata; print(importlib.metadata.version("responsaas"))')

install:
	poetry install

test:
	coverage run -m pytest src tests
	coverage combine
	coverage report
	coverage xml

lint:
	ruff src tests || exit 1
	mypy src tests || exit 1
	black --check --diff src tests || exit 1

format:
	ruff --fix src tests
	black src tests

readme-image:
	FORCE_COLOR=true python readme.py --help | ansitoimg --title '' docs/source/_static/example.svg
	
