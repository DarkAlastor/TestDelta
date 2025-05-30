PYTHONPATH=./src
APP_MODULE=src.app.main:app
UVICORN_OPTS=--reload --host 127.0.0.1 --port 8000

IMAGE_NAME_APP=parcel-service
IMAGE_NAME_WORKER=delivery-calculation-worker
IMAGE_NAME_CONSUMER=event-streamer
VERSION ?= latest


.PHONY: run
run:
	poetry run uvicorn $(APP_MODULE) $(UVICORN_OPTS)

.PHONY: test
test:
	poetry run pytest ./tests -v

.PHONY: test-api
test-api:
	poetry run pytest ./src/tests/api -v

.PHONY: test-unit
test-unit:
	poetry run pytest ./src/tests/unit -v

.PHONY: docker-clean
docker-clean:
	docker rmi -f $(IMAGE_NAME):$(VERSION) || true

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -r {} +

.PHONY: mypy
mypy:
	poetry run mypy src

.PHONY: ruff
ruff:
	poetry run ruff check src

.PHONY: ruff-fix
ruff-fix:
	poetry run ruff check src --fix

.PHONY: bandit
bandit:
	poetry run bandit -r src

.PHONY: lint
lint: ruff mypy bandit

.PHONY: init
init:
	@which poetry > /dev/null || (echo "Poetry not found. Installing..."; curl -sSL https://install.python-poetry.org | python3 -)
	poetry config virtualenvs.in-project true
	poetry install

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  run                   - Run local app with uvicorn"
	@echo "  test                  - Run all tests"
	@echo "  test-api              - Run all tests"
	@echo "  test-unit             - Run unit tests"
	@echo "  docker-clean          - Remove Docker image"
	@echo "  clean                 - Remove *.pyc and __pycache__"
	@echo "  mypy                  - Run type checks"
	@echo "  ruff                  - Run linter"
	@echo "  ruff-fix              - Run linter with auto-fix"
	@echo "  bandit                - Run security checks"
	@echo "  lint                  - Run all checks (ruff, mypy, bandit)"
	@echo "  init                  - Install poetry (if missing), create .venv, and install dependencies"