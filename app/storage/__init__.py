"""Tiv AI Storage Abstraction Package.

Provides a unified interface for storing raw contributions, canonical processed artifacts,
quarantine objects, and frozen dataset exports across local and cloud environments.
"""

from app.storage.base import StorageBackend
from app.storage.exceptions import (
    InvalidStorageKeyError,
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
    PathTraversalError,
    StorageError,
    StorageWriteError,
)
from app.storage.keys import (
    generate_export_key,
    generate_processed_audio_key,
    generate_quarantine_key,
    generate_raw_audio_key,
    is_immutable_namespace,
    validate_storage_key,
)
from app.storage.local import LocalStorageBackend
from app.storage.models import StoredObject
from app.storage.service import get_storage, reset_storage, set_storage_override

__all__ = [
    "StorageBackend",
    "StoredObject",
    "LocalStorageBackend",
    "get_storage",
    "set_storage_override",
    "reset_storage",
    "StorageError",
    "ObjectNotFoundError",
    "ObjectAlreadyExistsError",
    "InvalidStorageKeyError",
    "PathTraversalError",
    "StorageWriteError",
    "validate_storage_key",
    "is_immutable_namespace",
    "generate_raw_audio_key",
    "generate_processed_audio_key",
    "generate_quarantine_key",
    "generate_export_key",
]
