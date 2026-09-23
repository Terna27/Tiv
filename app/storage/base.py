"""Abstract base class definition for Tiv AI storage backends."""

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Generator, Optional, Union
from app.storage.models import StoredObject


class StorageBackend(ABC):
    """Abstract interface contract for storage backends across Tiv AI environments.
    
    Decouples application services from specific filesystem or cloud object storage APIs.
    """

    @abstractmethod
    def save(
        self,
        key: str,
        data: Union[BinaryIO, bytes],
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False,
    ) -> StoredObject:
        """Persist data stream or bytes to the given logical key.
        
        Args:
            key: Logical storage key (e.g. raw/audio/2026/09/sub_01.webm).
            data: Binary file-like stream or raw bytes.
            content_type: MIME type of the stored object.
            metadata: Optional key-value dictionary of custom metadata.
            overwrite: If False, raises ObjectAlreadyExistsError if key exists in raw/ namespace.
            
        Returns:
            StoredObject record containing verified key, size, checksum, and timestamp.
        """
        pass

    @abstractmethod
    def open_read(self, key: str) -> BinaryIO:
        """Open a read-only binary stream for the specified key.
        
        Raises:
            ObjectNotFoundError: If key does not exist.
            PathTraversalError: If key attempts to escape storage boundaries.
        """
        pass

    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        """Read and return all bytes for the specified key.
        
        Raises:
            ObjectNotFoundError: If key does not exist.
        """
        pass

    @abstractmethod
    def stream(self, key: str, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        """Stream chunks of bytes from storage to avoid loading large files into memory.
        
        Raises:
            ObjectNotFoundError: If key does not exist.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check whether an object exists at the specified key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete the object at the specified key.
        
        Raises:
            ObjectNotFoundError: If key does not exist.
        """
        pass

    @abstractmethod
    def get_metadata(self, key: str) -> StoredObject:
        """Retrieve stored object metadata (size, checksum, content type) without reading the full body.
        
        Raises:
            ObjectNotFoundError: If key does not exist.
        """
        pass
