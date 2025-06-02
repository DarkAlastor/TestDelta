PYTHONPATH=./src
APP_MODULE=src.parcel_service.main:app
UVICORN_OPTS=--reload --host 127.0.0.1 --port 8000

IMAGE_NAME_APP=parcel-service
IMAGE_NAME_WORKER=delivery-calculation-worker
IMAGE_NAME_CONSUMER=event-streamer
VERSION ?= latest


.PHONY: run
run:
	poetry run uvicorn $(APP_MODULE) $(UVICORN_OPTS)

.PHONY: run-publisher
run-publisher:
	PYTHONPATH=. poetry run python3 src/outbox_publisher/main.py

.PHONY: run-calculation
run-calculation:
	PYTHONPATH=. poetry run python3 src/delivery_calculation_worker/main.py

.PHONY: test
test:
	poetry run pytest ./tests

.PHONY: docker-clean
docker-clean:
	docker rmi -f $(IMAGE_NAME):$(VERSION) || true

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -r {} +

.PHONY: ruff-fix
ruff-fix:
	poetry run ruff check src --fix

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
	@echo "  docker-clean          - Remove Docker image"
	@echo "  clean                 - Remove *.pyc and __pycache__"
	@echo "  ruff-fix              - Run linter with auto-fix"
	@echo "  lint                  - Run all checks (ruff, mypy, bandit)"
	@echo "  init                  - Install poetry (if missing), create .venv, and install dependencies"