.PHONY: install install-dev lint format test test-cov run clean setup pre-commit

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	PYTHONPATH=. pytest

test-cov:
	PYTHONPATH=. pytest --cov=. --cov-report=term --cov-report=xml

test-quick:
	PYTHONPATH=. pytest tests/ -x -q --ignore=tests/test_ensemble_get_model_prediction.py

run:
	streamlit run app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov

setup: install install-dev pre-commit

pre-commit:
	pre-commit install
	pre-commit run --all-files

docker-build:
	docker build -t spamlyser:latest .

docker-run:
	docker run -p 8501:8501 spamlyser:latest

security:
	pip-audit -r requirements.txt
	bandit -r . --exclude ./tests,./docs,.venv -l -i
