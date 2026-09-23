#!/usr/bin/env python3
"""Lightweight local development environment verification script (Milestone 1).

Checks Python version, dependencies, environment configuration, database connectivity,
and local storage directory writability.
"""

import sys
import importlib
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_python_version() -> bool:
    print(f"[*] Python Version: {sys.version.split()[0]}", end=" ")
    if sys.version_info >= (3, 12):
        print("✓ (Compatible: >= 3.12)")
        return True
    print("✗ (Warning: Python >= 3.12 recommended)")
    return False


def check_dependencies() -> bool:
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "alembic",
        "httpx",
        "pytest",
    ]
    all_ok = True
    print("[*] Checking core dependencies:")
    for mod in required:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"    - {mod} ({ver}) ✓")
        except ImportError:
            print(f"    - {mod} ✗ MISSING")
            all_ok = False
    return all_ok


def check_storage_directories() -> bool:
    print("[*] Checking local storage preparation:")
    from app.storage_prep import ensure_local_storage_directories
    from app.config import settings

    res = ensure_local_storage_directories(settings.LOCAL_STORAGE_PATH)
    if res.get("writable"):
        print(f"    - Root path: {res['root_path']} ✓")
        print(f"    - Writable: Yes ✓")
        print(f"    - Namespaces: {', '.join(res['namespaces'])} ✓")
        return True
    else:
        print(f"    - Root path: {res['root_path']} ✗ Not writable")
        return False


def check_database() -> bool:
    print("[*] Checking database connectivity:")
    from app.database import check_db_connectivity

    res = check_db_connectivity()
    if res.get("status") == "connected":
        print(f"    - Dialect: {res.get('dialect')} ✓")
        print(f"    - Host: {res.get('host')} ✓")
        print(f"    - Database: {res.get('database')} ✓")
        return True
    else:
        print(f"    - Status: ✗ Failed ({res.get('error')})")
        return False


def check_backend_running() -> bool:
    print("[*] Checking running backend on localhost:8000:")
    try:
        import httpx
        with httpx.Client(timeout=2.0) as client:
            resp = client.get("http://127.0.0.1:8000/api/v1/health")
            if resp.status_code == 200:
                print(f"    - GET /api/v1/health: 200 OK ✓")
                return True
            else:
                print(f"    - GET /api/v1/health: HTTP {resp.status_code} ✗")
                return False
    except Exception:
        print("    - Backend not currently running (start with: make run-backend)")
        return False


def main():
    print("=" * 60)
    print("Tiv AI Platform — Development Environment Health Check")
    print("=" * 60)

    p_ok = check_python_version()
    d_ok = check_dependencies()
    s_ok = check_storage_directories()
    db_ok = check_database()
    check_backend_running()

    print("=" * 60)
    if p_ok and d_ok and s_ok and db_ok:
        print("RESULT: Local development environment is READY! ✓")
        sys.exit(0)
    else:
        print("RESULT: Environment has issues. Please fix errors above. ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
