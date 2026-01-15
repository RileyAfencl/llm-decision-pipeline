.PHONY: lint test check

lint:
	python -m ruff check .

test:
	python -m pytest -q

check: lint test
