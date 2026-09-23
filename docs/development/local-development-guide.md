# Local Development Environment Guide (Milestone 1)

This guide documents the verified, reproducible setup procedure for running the **Tiv AI Data Collection Platform** on a local development machine.

---

## 1. System Prerequisites

Before starting, verify that the following system tools are installed:

| Tool | Minimum Version | Verified Local Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `>= 3.12` | `Python 3.12.3` | Backend runtime & data pipeline |
| **Node.js** | `>= 20.0.0` | `v24.20.0` | Frontend Vite dev server |
| **npm** | `>= 10.0.0` | `11.19.0` | Frontend package manager |
| **Git** | `>= 2.30.0` | `2.43.0` | Source control |
| **Make** | Any standard POSIX | `GNU Make 4.3` | Developer command runner |

---

## 2. Quickstart Workflow (Using Make)

From the root of the cloned repository:

```bash
# 1. Initialize environment, install dependencies, prepare .env & storage
make setup

# 2. Run diagnostic health verification
make verify

# 3. Execute backend automated test suite
make test

# 4. Start the FastAPI backend server (http://127.0.0.1:8000)
make run-backend
```

In a separate terminal, to start the frontend:
```bash
# Unpack frontend workspace & install npm packages
make frontend-setup

# Start Vite development server (http://localhost:5173)
make frontend-dev
```

---

## 3. Step-by-Step Manual Setup

If you prefer executing the underlying commands directly without `make`:

### Step 3.1: Python Virtual Environment Setup
```bash
# Create isolated Python virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install all backend and testing dependencies
pip install -r requirements.txt
```

### Step 3.2: Environment Configuration (`.env`)
Copy the committed template `.env.example` to create your local `.env`:
```bash
cp .env.example .env
```

The default values in `.env.example` are pre-configured for zero-friction local development:
* `ENVIRONMENT=development`
* `HOST=0.0.0.0`
* `PORT=8000`
* `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
* `DATABASE_URL=sqlite:///./tiv_ai_dev.db` (or PostgreSQL if running locally)
* `STORAGE_BACKEND=local`
* `LOCAL_STORAGE_PATH=.storage`

> [!CAUTION] Security Rule
> Never commit `.env` or any real credentials to version control. The `.gitignore` file strictly excludes `.env` and local database/storage files.

### Step 3.3: Database Setup & Migrations
The backend supports two database backends:
1. **SQLite (Default for Localhost)**: Zero-configuration file database located at `./tiv_ai_dev.db` (auto-created on startup).
2. **PostgreSQL**: When PostgreSQL is running, update `DATABASE_URL` in `.env`:
   ```bash
   DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/tiv_ai
   ```

To run Alembic schema migrations:
```bash
alembic upgrade head
```

To check current migration state:
```bash
alembic current
```

### Step 3.4: Local Storage Preparation
The local storage namespaces are created automatically on application startup. You can also initialize them manually:
```bash
python3 -c "from app.storage_prep import ensure_local_storage_directories; ensure_local_storage_directories()"
```
This ensures the following directories exist under `.storage/`:
* `raw/audio`: For immutable original audio uploads.
* `processed/audio`: For normalized 16 kHz mono WAV derivatives.
* `quarantine`: For corrupted, truncated, or invalid uploads.
* `exports/datasets`: For frozen versioned dataset packages.

### Step 3.5: Run Backend Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend health:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected JSON response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "connected",
    "dialect": "sqlite",
    "host": "localhost",
    "database": "./tiv_ai_dev.db"
  },
  "storage": {
    "backend": "local",
    "root_path": ".../.storage",
    "writable": true,
    "namespaces": ["raw/audio", "processed/audio", "quarantine", "exports/datasets"]
  },
  "audio_constraints": {
    "max_size_bytes": 26214400,
    "min_duration_seconds": 0.5,
    "max_duration_seconds": 120.0
  },
  "consent_version": "v1.0-2026-09"
}
```

---

## 4. Frontend Integration (Developer 2)

Developer 2's frontend is located in `tiv-ai-frontend.zip`. To run it locally alongside the backend:

```bash
# 1. Unzip frontend code
unzip -qo tiv-ai-frontend.zip

# 2. Install dependencies
cd tiv-ai-frontend
npm install

# 3. Start development server
npm run dev
```

* **Frontend URL**: `http://localhost:5173`
* **API Configuration**: The frontend API client (`src/api/client.js`) connects to `http://localhost:8000/api/v1` by default.
* **CORS**: The FastAPI backend includes `CORSMiddleware` pre-configured to allow `http://localhost:5173`.
* **Mock Toggle**: In `src/api/client.js`, set `USE_MOCKS = false` (or toggle individual entries in `MOCK_ENDPOINTS`) to communicate with the live backend endpoints.

---

## 5. Automated Verification & Testing

Run the full automated backend test suite:
```bash
pytest -v
```

All 5 core environment tests should pass:
1. `test_root_endpoint`: Verifies `/` metadata and OpenAPI docs pointer.
2. `test_health_endpoint`: Verifies `/api/v1/health` reports status `ok` and connected database.
3. `test_cors_headers`: Verifies `Access-Control-Allow-Origin: http://localhost:5173`.
4. `test_docs_endpoint`: Verifies `/docs` (FastAPI Swagger UI) loads.
5. `test_storage_namespaces_exist`: Verifies all four local storage namespaces exist and are writable.

Run the development environment health diagnostic:
```bash
python scripts/verify_dev_env.py
```

---

## 6. Local Development Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'app'` | Virtual environment not active or root directory not in path | Run `source .venv/bin/activate` from the repository root. |
| `database connection error (PostgreSQL)` | Local PostgreSQL service is stopped | Start PostgreSQL or keep `DATABASE_URL=sqlite:///./tiv_ai_dev.db` in `.env`. |
| `CORS Error in Browser Console` | Frontend running on non-standard port | Add your frontend port to `CORS_ORIGINS` in `.env` (e.g. `http://localhost:3000`). |
| `Address already in use: 8000` | Another process is holding port 8000 | Kill existing process with `lsof -i :8000 \| awk 'NR>1 {print $2}' \| xargs kill -9` or change `PORT=8001` in `.env`. |
