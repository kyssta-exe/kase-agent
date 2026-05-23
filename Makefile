.PHONY: install install-dev install-all lint test clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[anthropic,dev,messaging]"

lint:
	ruff check kase/

test:
	pytest -xvs

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
