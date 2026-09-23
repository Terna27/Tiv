# ==============================================================================
# Tiv AI Data Collection Platform — Developer Workflow Makefile
# ==============================================================================

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
UVICORN ?= .venv/bin/uvicorn
ALEMBIC ?= .venv/bin/alembic
PYTEST ?= .venv/bin/pytest

.PHONY: help setup run-backend migrate test verify frontend-setup frontend-dev clean

help:
	@echo "Tiv AI Data Collection Platform — Developer Commands:"
	@echo "  make setup          - Initialize virtualenv, install dependencies, prepare .env & storage"
	@echo "  make run-backend    - Run FastAPI backend on http://127.0.0.1:8000 (auto-reload)"
	@echo "  make migrate        - Run database migrations via Alembic"
	@echo "  make test           - Run backend test suite via pytest"
	@echo "  make verify         - Run development environment health check"
	@echo "  make frontend-setup - Unpack Developer 2 frontend and install npm packages"
	@echo "  make frontend-dev   - Run Developer 2 frontend Vite dev server (http://localhost:5173)"
	@echo "  make clean          - Remove temporary Python caches and test artifacts"

setup:
	@echo "[*] Creating Python virtual environment if missing..."
	@test -d .venv || python3 -m venv .venv
	@echo "[*] Installing Python backend dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "[*] Creating .env from .env.example if missing..."
	@test -f .env || cp .env.example .env
	@echo "[*] Initializing local storage namespaces..."
	@$(PYTHON) -c "from app.storage_prep import ensure_local_storage_directories; ensure_local_storage_directories()"
	@echo "[✓] Setup complete! Run 'make verify' to confirm environment readiness."

run-backend:
	$(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8000

migrate:
	$(ALEMBIC) upgrade head

test:
	$(PYTEST) -v

verify:
	$(PYTHON) scripts/verify_dev_env.py

frontend-setup:
	@echo "[*] Unpacking frontend archive..."
	@test -d tiv-ai-frontend || unzip -qo tiv-ai-frontend.zip
	@echo "[*] Installing frontend npm packages..."
	@cd tiv-ai-frontend && npm install
	@echo "[✓] Frontend setup complete! Run 'make frontend-dev' to start."

frontend-dev:
	@test -d tiv-ai-frontend || $(MAKE) frontend-setup
	@cd tiv-ai-frontend && npm run dev

clean:
	rm -rf __pycache__ app/__pycache__ tests/__pycache__ scripts/__pycache__
	rm -rf .pytest_cache
	rm -f tiv_ai_dev.db
