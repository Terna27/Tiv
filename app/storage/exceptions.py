"""Storage exception hierarchy for Tiv AI Data Collection Platform."""


class StorageError(Exception):
    """Base exception for all storage-related operations."""
    pass


class ObjectNotFoundError(StorageError):
    """Raised when an requested object key does not exist in storage."""

    def __init__(self, key: str, message: str = None):
        self.key = key
        super().__init__(message or f"Storage object not found: '{key}'")


class ObjectAlreadyExistsError(StorageError):
    """Raised when attempting to overwrite an object in an immutable namespace (e.g. raw/)."""

    def __init__(self, key: str, message: str = None):
        self.key = key
        super().__init__(
            message or f"Storage object already exists and cannot be overwritten (immutable): '{key}'"
        )


class InvalidStorageKeyError(StorageError):
    """Raised when a storage key fails format, naming, or security validation."""

    def __init__(self, key: str, reason: str = None):
        self.key = key
        self.reason = reason
        msg = f"Invalid storage key '{key}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class PathTraversalError(InvalidStorageKeyError):
    """Raised when a storage key attempts to escape the root storage directory."""

    def __init__(self, key: str):
        super().__init__(key, reason="Path traversal outside storage root detected")


class StorageWriteError(StorageError):
    """Raised when atomic write, disk persistence, or stream serialization fails."""
    pass
