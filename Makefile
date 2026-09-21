# ============================================================
# Makefile — Student-Document-OCR (Placeholder)
# ============================================================
# TODO: Implement actual targets as development progresses.
# Usage: make <target>
# ============================================================

.PHONY: help setup install dev test lint format clean docker-up docker-down \
        migrate seed train eval docs

# ── Default ──────────────────────────────────────────────────
.DEFAULT_GOAL := help

# ── Colors ───────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
RESET  := \033[0m

help: ## Show this help message
	@echo "$(CYAN)════════════════════════════════════════$(RESET)"
	@echo "$(CYAN)  Student-Document-OCR — Make Targets   $(RESET)"
	@echo "$(CYAN)════════════════════════════════════════$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# ── Environment Setup ────────────────────────────────────────
setup: ## Create virtualenv and install dependencies
	# TODO: python -m venv .venv && pip install -e .[dev]
	@echo "$(YELLOW)[TODO] Implement: setup$(RESET)"

install: ## Install Python dependencies
	# TODO: pip install -r requirements.txt
	@echo "$(YELLOW)[TODO] Implement: install$(RESET)"

env: ## Copy .env.example to .env
	cp .env.example .env
	@echo "$(GREEN).env created from .env.example$(RESET)"

# ── Development ──────────────────────────────────────────────
dev: ## Start backend dev server (uvicorn --reload)
	# TODO: uvicorn backend.app.main:app --reload --port 8000
	@echo "$(YELLOW)[TODO] Implement: dev$(RESET)"

dev-frontend: ## Start frontend dev server (Vite)
	# TODO: cd frontend && npm run dev
	@echo "$(YELLOW)[TODO] Implement: dev-frontend$(RESET)"

dev-worker: ## Start Celery worker
	# TODO: celery -A backend.app.worker worker --loglevel=info
	@echo "$(YELLOW)[TODO] Implement: dev-worker$(RESET)"

# ── Database ─────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	# TODO: alembic upgrade head
	@echo "$(YELLOW)[TODO] Implement: migrate$(RESET)"

migrate-create: ## Create a new migration (NAME=description)
	# TODO: alembic revision --autogenerate -m "$(NAME)"
	@echo "$(YELLOW)[TODO] Implement: migrate-create$(RESET)"

seed: ## Seed the database with sample data
	# TODO: python scripts/seed_db.py
	@echo "$(YELLOW)[TODO] Implement: seed$(RESET)"

# ── Testing ──────────────────────────────────────────────────
test: ## Run all tests with coverage
	# TODO: pytest --cov=backend/app --cov-report=html
	@echo "$(YELLOW)[TODO] Implement: test$(RESET)"

test-unit: ## Run unit tests only
	# TODO: pytest tests/unit/
	@echo "$(YELLOW)[TODO] Implement: test-unit$(RESET)"

test-integration: ## Run integration tests
	# TODO: pytest tests/integration/
	@echo "$(YELLOW)[TODO] Implement: test-integration$(RESET)"

test-ocr: ## Run OCR-specific tests
	# TODO: pytest tests/ocr/
	@echo "$(YELLOW)[TODO] Implement: test-ocr$(RESET)"

# ── Code Quality ─────────────────────────────────────────────
lint: ## Run Ruff linter
	# TODO: ruff check .
	@echo "$(YELLOW)[TODO] Implement: lint$(RESET)"

format: ## Run Ruff formatter
	# TODO: ruff format .
	@echo "$(YELLOW)[TODO] Implement: format$(RESET)"

typecheck: ## Run MyPy type checker
	# TODO: mypy backend/app
	@echo "$(YELLOW)[TODO] Implement: typecheck$(RESET)"

# ── Docker ───────────────────────────────────────────────────
docker-up: ## Start all Docker services
	# TODO: docker compose up -d
	@echo "$(YELLOW)[TODO] Implement: docker-up$(RESET)"

docker-down: ## Stop all Docker services
	# TODO: docker compose down
	@echo "$(YELLOW)[TODO] Implement: docker-down$(RESET)"

docker-logs: ## Follow Docker service logs
	# TODO: docker compose logs -f
	@echo "$(YELLOW)[TODO] Implement: docker-logs$(RESET)"

docker-build: ## Build all Docker images
	# TODO: docker compose build --no-cache
	@echo "$(YELLOW)[TODO] Implement: docker-build$(RESET)"

# ── AI / Training ────────────────────────────────────────────
train: ## Start model training
	# TODO: python training/train.py --config training/config.yaml
	@echo "$(YELLOW)[TODO] Implement: train$(RESET)"

eval: ## Evaluate trained model
	# TODO: python training/evaluate.py --checkpoint models/best.pth
	@echo "$(YELLOW)[TODO] Implement: eval$(RESET)"

# ── Elasticsearch ────────────────────────────────────────────
es-index: ## Create Elasticsearch index mappings
	# TODO: python scripts/es_create_index.py
	@echo "$(YELLOW)[TODO] Implement: es-index$(RESET)"

es-reindex: ## Reindex all documents
	# TODO: python scripts/es_reindex.py
	@echo "$(YELLOW)[TODO] Implement: es-reindex$(RESET)"

# ── Documentation ────────────────────────────────────────────
docs: ## Build project documentation
	# TODO: mkdocs build
	@echo "$(YELLOW)[TODO] Implement: docs$(RESET)"

# ── Cleanup ──────────────────────────────────────────────────
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__     -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache     -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache     -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"         -delete 2>/dev/null || true
	@echo "$(GREEN)Cleaned build artifacts$(RESET)"
