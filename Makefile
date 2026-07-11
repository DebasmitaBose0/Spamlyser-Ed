.PHONY: install install-dev lint format test test-cov run clean setup pre-commit docker-build docker-run docker-compose-up docker-compose-down

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

run:
	streamlit run app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .coverage coverage.xml htmlcov

setup: install install-dev pre-commit

pre-commit:
	pre-commit install
	pre-commit run --all-files

docker-build:
	docker build -t spamlyser:latest .

docker-run:
	docker run -p 8501:8501 spamlyser:latest

docker-compose-up:
	docker compose up -d --build

docker-compose-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-health:
	docker compose exec spamlyser python healthcheck.py

security:
	pip-audit -r requirements.txt
	bandit -r . --exclude ./tests,./docs,.venv -l -i
