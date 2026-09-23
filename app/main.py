"""FastAPI Application entry point for Tiv AI Data Collection Platform."""

from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings
from app.database import check_db_connectivity
from app.storage_prep import ensure_local_storage_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initialization and graceful teardown."""
    # Initialize local storage directories if running on local backend
    if settings.STORAGE_BACKEND == "local":
        ensure_local_storage_directories(settings.LOCAL_STORAGE_PATH)
    yield


app = FastAPI(
    title="Tiv AI Data Collection Platform API",
    description="Production-grade ingestion, validation, and review API for Tiv text, translations, and speech audio.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for Developer 2 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root() -> Dict[str, Any]:
    """Root metadata and developer documentation pointer."""
    return {
        "name": "Tiv AI Data Collection Platform API",
        "version": __version__,
        "documentation": "/docs",
        "health": "/api/v1/health",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/v1/health", tags=["Health"])
@app.get("/health", tags=["Health"], include_in_schema=False)
def health_check() -> JSONResponse:
    """Comprehensive health check verifying runtime, database connectivity, and local storage state."""
    db_status = check_db_connectivity()

    storage_status: Dict[str, Any] = {"backend": settings.STORAGE_BACKEND}
    if settings.STORAGE_BACKEND == "local":
        storage_status.update(ensure_local_storage_directories(settings.LOCAL_STORAGE_PATH))
    else:
        storage_status["bucket"] = settings.S3_BUCKET_NAME
        storage_status["region"] = settings.S3_REGION

    overall_healthy = db_status.get("status") == "connected"
    if settings.STORAGE_BACKEND == "local":
        overall_healthy = overall_healthy and storage_status.get("writable", False)

    status_code = 200 if overall_healthy else 503

    payload = {
        "status": "ok" if overall_healthy else "degraded",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "storage": storage_status,
        "audio_constraints": {
            "max_size_bytes": settings.MAX_AUDIO_SIZE_BYTES,
            "min_duration_seconds": settings.MIN_AUDIO_DURATION_SECONDS,
            "max_duration_seconds": settings.MAX_AUDIO_DURATION_SECONDS,
        },
        "consent_version": settings.CONSENT_VERSION,
    }

    return JSONResponse(status_code=status_code, content=payload)
