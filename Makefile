.PHONY: install install-dev run test lint clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install -q -r requirements.txt

install-dev: $(VENV)/bin/activate
	$(PIP) install -q -r requirements.txt -r requirements-dev.txt

run: install
	$(PYTHON) -m bot.main

test: install-dev
	$(VENV)/bin/pytest tests/ -v

lint: install-dev
	$(VENV)/bin/ruff check bot/ tests/ || true

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache support.db
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
