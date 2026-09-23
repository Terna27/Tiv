"""Database session management and connectivity verification."""

from typing import Generator, Dict, Any
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Construct engine with dialect-specific connection arguments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for scoped transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity() -> Dict[str, Any]:
    """Check database connectivity for health check and diagnostics."""
    try:
        parsed = urlparse(settings.DATABASE_URL)
        dialect = parsed.scheme.split("+")[0] if parsed.scheme else "unknown"
        # Mask credentials in host/URL display
        masked_host = parsed.hostname or "localhost"
        if parsed.port:
            masked_host = f"{masked_host}:{parsed.port}"

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "dialect": dialect,
            "host": masked_host,
            "database": parsed.path.lstrip("/") or "in_memory",
        }
    except Exception as exc:
        return {
            "status": "error",
            "dialect": dialect if "dialect" in locals() else "unknown",
            "error": str(exc),
        }
