"""Central storage factory and service provider."""

from typing import Optional
from app.config import settings
from app.storage.base import StorageBackend
from app.storage.exceptions import StorageError
from app.storage.local import LocalStorageBackend

_storage_instance: Optional[StorageBackend] = None


def get_storage(backend_type: Optional[str] = None) -> StorageBackend:
    """Obtain the configured StorageBackend instance.
    
    Acts as a central service locator and FastAPI dependency provider.
    Application code depends solely on the StorageBackend interface, never on concrete providers.
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    selected_backend = backend_type or settings.STORAGE_BACKEND.lower()

    if selected_backend == "local":
        _storage_instance = LocalStorageBackend(root_dir=settings.LOCAL_STORAGE_PATH)
        return _storage_instance
    elif selected_backend == "s3":
        raise StorageError(
            "Production S3 storage provider is scheduled for cloud deployment. "
            "Set STORAGE_BACKEND=local for local development and testing."
        )
    else:
        raise StorageError(f"Unsupported storage backend: '{selected_backend}'. Allowed: ['local', 's3']")


def set_storage_override(backend: Optional[StorageBackend]) -> None:
    """Set or clear a storage backend instance override for testing isolation."""
    global _storage_instance
    _storage_instance = backend


def reset_storage() -> None:
    """Reset the cached storage instance."""
    global _storage_instance
    _storage_instance = None
