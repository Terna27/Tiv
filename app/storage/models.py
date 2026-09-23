"""Storage domain models and object representations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass(frozen=True)
class StoredObject:
    """Safe, immutable representation of an object stored in the Tiv AI platform.
    
    Contains only authoritative storage metadata (key, size, checksum, content-type).
    Does NOT contain machine-specific absolute filesystem paths or media parameters.
    """

    key: str
    size_bytes: int
    content_type: str
    checksum_sha256: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    custom_metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize storage object metadata to a dictionary."""
        return {
            "key": self.key,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "checksum_sha256": self.checksum_sha256,
            "created_at": self.created_at.isoformat(),
            "custom_metadata": self.custom_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredObject":
        """Deserialize storage object metadata from a dictionary."""
        created_at_val = data.get("created_at")
        if isinstance(created_at_val, str):
            created_at = datetime.fromisoformat(created_at_val)
        elif isinstance(created_at_val, datetime):
            created_at = created_at_val
        else:
            created_at = datetime.now(timezone.utc)

        return cls(
            key=data["key"],
            size_bytes=int(data["size_bytes"]),
            content_type=data.get("content_type", "application/octet-stream"),
            checksum_sha256=data["checksum_sha256"],
            created_at=created_at,
            custom_metadata=data.get("custom_metadata", {}),
        )
