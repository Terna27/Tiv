"""Local filesystem storage backend with atomic writes and path traversal defense."""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Dict, Generator, Optional, Union

from app.storage.base import StorageBackend
from app.storage.exceptions import (
    InvalidStorageKeyError,
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
    PathTraversalError,
    StorageWriteError,
)
from app.storage.keys import is_immutable_namespace, validate_storage_key
from app.storage.models import StoredObject


class LocalStorageBackend(StorageBackend):
    """Local filesystem implementation of the Tiv AI StorageBackend.
    
    Guarantees:
    1. Root containment: Rejects any path traversal escaping the configured root directory.
    2. Atomic writes: Streams to temporary files before atomic rename; cleans up on failure.
    3. Immutability: Rejects overwriting objects in immutable namespaces (e.g. raw/).
    4. Streaming integrity: Generates SHA-256 checksums on-the-fly during write.
    """

    def __init__(self, root_dir: Union[str, Path]):
        self.root_path = Path(root_dir).resolve()
        self.root_path.mkdir(parents=True, exist_ok=True)
        # Directory for staging atomic writes on the same filesystem
        self.tmp_path = self.root_path / ".tmp"
        self.tmp_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolve and validate logical storage key against storage root.
        
        Raises:
            InvalidStorageKeyError: If key syntax is invalid.
            PathTraversalError: If key attempts to escape storage root.
        """
        validated_key = validate_storage_key(key)
        target_path = (self.root_path / validated_key).resolve()

        try:
            target_path.relative_to(self.root_path)
        except ValueError:
            raise PathTraversalError(key)

        if target_path == self.root_path:
            raise InvalidStorageKeyError(key, "Target cannot be the storage root directory")

        return target_path

    def _meta_path(self, target_path: Path) -> Path:
        """Return the companion metadata file path for a stored object."""
        return target_path.with_name(f".{target_path.name}.meta.json")

    def save(
        self,
        key: str,
        data: Union[BinaryIO, bytes],
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False,
    ) -> StoredObject:
        """Persist data stream or bytes to key atomically with on-the-fly SHA-256 computation."""
        target_path = self._resolve_path(key)

        # Immutability enforcement (raw/ namespace is strictly write-once)
        if is_immutable_namespace(key) and target_path.is_file():
            raise ObjectAlreadyExistsError(
                key,
                f"Object '{key}' exists in immutable namespace '{key.split('/')[0]}/' and cannot be overwritten",
            )

        if not overwrite and target_path.is_file():
            raise ObjectAlreadyExistsError(key, f"Object '{key}' already exists (overwrite=False)")

        # Ensure destination directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256()
        bytes_written = 0
        temp_file = None
        temp_path = None

        try:
            # Create temporary file in the storage staging area
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.tmp_path,
                prefix="tmp_upload_",
                delete=False,
            )
            temp_path = Path(temp_file.name)

            if isinstance(data, bytes):
                hasher.update(data)
                temp_file.write(data)
                bytes_written = len(data)
            else:
                chunk_size = 65536
                while True:
                    chunk = data.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    temp_file.write(chunk)
                    bytes_written += len(chunk)

            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()

            # Atomic rename from staging path to destination path
            os.replace(temp_path, target_path)

            checksum = hasher.hexdigest()
            created_at = datetime.now(timezone.utc)
            stored_obj = StoredObject(
                key=key,
                size_bytes=bytes_written,
                content_type=content_type,
                checksum_sha256=checksum,
                created_at=created_at,
                custom_metadata=metadata or {},
            )

            # Write companion metadata atomically
            meta_path = self._meta_path(target_path)
            meta_tmp = tempfile.NamedTemporaryFile(
                dir=self.tmp_path,
                prefix="tmp_meta_",
                delete=False,
            )
            meta_tmp_path = Path(meta_tmp.name)
            meta_tmp.write(json.dumps(stored_obj.to_dict(), indent=2).encode("utf-8"))
            meta_tmp.flush()
            os.fsync(meta_tmp.fileno())
            meta_tmp.close()
            os.replace(meta_tmp_path, meta_path)

            return stored_obj

        except Exception as exc:
            # Clean up temp file on failure to avoid leaking temporary artifacts
            if temp_file and not temp_file.closed:
                try:
                    temp_file.close()
                except Exception:
                    pass
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            if isinstance(exc, (ObjectAlreadyExistsError, InvalidStorageKeyError)):
                raise
            raise StorageWriteError(f"Failed to atomically write object '{key}': {exc}") from exc

    def open_read(self, key: str) -> BinaryIO:
        """Open a read-only binary stream for the specified key."""
        target_path = self._resolve_path(key)
        if not target_path.is_file():
            raise ObjectNotFoundError(key)
        try:
            return open(target_path, "rb")
        except OSError as exc:
            raise ObjectNotFoundError(key, f"Cannot open storage object '{key}': {exc}") from exc

    def read_bytes(self, key: str) -> bytes:
        """Read and return all bytes for the specified key."""
        with self.open_read(key) as stream:
            return stream.read()

    def stream(self, key: str, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        """Stream chunks of bytes from storage without loading the whole object into RAM."""
        with self.open_read(key) as stream:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def exists(self, key: str) -> bool:
        """Check whether an object exists at the specified key."""
        try:
            target_path = self._resolve_path(key)
            return target_path.is_file()
        except InvalidStorageKeyError:
            return False

    def delete(self, key: str) -> bool:
        """Delete object and its companion metadata.
        
        Strictly used for quarantine cleanup or consent withdrawal erasure.
        """
        target_path = self._resolve_path(key)
        if not target_path.is_file():
            raise ObjectNotFoundError(key)

        target_path.unlink()
        meta_path = self._meta_path(target_path)
        if meta_path.is_file():
            meta_path.unlink()
        return True

    def get_metadata(self, key: str) -> StoredObject:
        """Retrieve technical metadata for the specified key."""
        target_path = self._resolve_path(key)
        if not target_path.is_file():
            raise ObjectNotFoundError(key)

        meta_path = self._meta_path(target_path)
        if meta_path.is_file():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                return StoredObject.from_dict(data)
            except Exception:
                pass  # Fall back to file stat and checksum computation

        # Fallback: compute dynamically if companion metadata missing
        size_bytes = target_path.stat().st_size
        hasher = hashlib.sha256()
        with open(target_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

        mtime = datetime.fromtimestamp(target_path.stat().st_mtime, tz=timezone.utc)
        return StoredObject(
            key=key,
            size_bytes=size_bytes,
            content_type="application/octet-stream",
            checksum_sha256=hasher.hexdigest(),
            created_at=mtime,
            custom_metadata={},
        )
