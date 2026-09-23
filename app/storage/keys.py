"""Safe storage key generation and validation utilities."""

import re
from datetime import datetime, timezone
from typing import Optional
from app.storage.exceptions import InvalidStorageKeyError, PathTraversalError


IMMUTABLE_NAMESPACES = ("raw/",)
ALLOWED_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\./]+$")
SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_storage_key(key: str) -> str:
    """Validate and sanitize a logical storage key.
    
    Prevents path traversal, absolute paths, null bytes, and malicious characters.
    Returns the normalized key if valid, or raises an appropriate storage exception.
    """
    if not key or not isinstance(key, str):
        raise InvalidStorageKeyError(str(key), "Key must be a non-empty string")

    # Reject null bytes
    if "\x00" in key:
        raise InvalidStorageKeyError(key, "Null byte in storage key")

    # Reject absolute paths and Windows backslashes
    if key.startswith("/") or "\\" in key:
        raise InvalidStorageKeyError(key, "Absolute paths and backslashes are disallowed")

    # Check for path traversal components
    parts = key.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise PathTraversalError(key)

    # Validate against allowed character set
    if not ALLOWED_KEY_PATTERN.match(key):
        raise InvalidStorageKeyError(key, "Key contains invalid characters")

    return key


def is_immutable_namespace(key: str) -> bool:
    """Check if the given key belongs to an immutable namespace where overwrites are prohibited."""
    return any(key.startswith(ns) for ns in IMMUTABLE_NAMESPACES)


def sanitize_filename_component(component: str, default: str = "unnamed") -> str:
    """Sanitize an identifier component (such as submission_id or reason)."""
    if not component:
        return default
    # Strip any characters that aren't alphanumeric, underscore, or hyphen
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", component).strip("_")
    return cleaned or default


def sanitize_extension(extension: str, default: str = "bin") -> str:
    """Sanitize and normalize a file extension."""
    if not extension:
        return default
    cleaned = extension.lstrip(".").lower()
    cleaned = re.sub(r"[^a-z0-9]", "", cleaned)
    return cleaned or default


def generate_raw_audio_key(
    submission_id: str,
    content_hash: str,
    extension: str,
    timestamp: Optional[datetime] = None,
) -> str:
    """Generate a collision-resistant, date-partitioned storage key for raw contributed audio.
    
    Pattern: raw/audio/{YYYY}/{MM}/{DD}/{submission_id}_{hash_prefix}.{extension}
    Example: raw/audio/2026/09/23/sub_01h8q7j4_a1b2c3d4.webm
    """
    ts = timestamp or datetime.now(timezone.utc)
    safe_sub_id = sanitize_filename_component(submission_id, "sub_unknown")
    clean_hash = re.sub(r"[^a-fA-F0-9]", "", content_hash)[:8].lower() or "00000000"
    safe_ext = sanitize_extension(extension, "webm")

    date_path = ts.strftime("%Y/%m/%d")
    raw_key = f"raw/audio/{date_path}/{safe_sub_id}_{clean_hash}.{safe_ext}"
    return validate_storage_key(raw_key)


def generate_processed_audio_key(
    submission_id: str,
    tag: str = "16k_mono",
    extension: str = "wav",
    timestamp: Optional[datetime] = None,
) -> str:
    """Generate a storage key for derived processed audio artifacts.
    
    Pattern: processed/audio/{YYYY}/{MM}/{submission_id}_{tag}.{extension}
    Example: processed/audio/2026/09/sub_01h8q7j4_16k_mono.wav
    """
    ts = timestamp or datetime.now(timezone.utc)
    safe_sub_id = sanitize_filename_component(submission_id, "sub_unknown")
    safe_tag = sanitize_filename_component(tag, "derivative")
    safe_ext = sanitize_extension(extension, "wav")

    date_path = ts.strftime("%Y/%m")
    key = f"processed/audio/{date_path}/{safe_sub_id}_{safe_tag}.{safe_ext}"
    return validate_storage_key(key)


def generate_quarantine_key(
    quarantine_id: str,
    reason: str = "malformed",
    timestamp: Optional[datetime] = None,
) -> str:
    """Generate a storage key for quarantined uploads.
    
    Pattern: quarantine/{YYYY}/{MM}/{quarantine_id}_{reason}.bin
    """
    ts = timestamp or datetime.now(timezone.utc)
    safe_id = sanitize_filename_component(quarantine_id, "quarantine")
    safe_reason = sanitize_filename_component(reason, "invalid")

    date_path = ts.strftime("%Y/%m")
    key = f"quarantine/{date_path}/{safe_id}_{safe_reason}.bin"
    return validate_storage_key(key)


def generate_export_key(dataset_version: str, filename: str) -> str:
    """Generate a storage key for frozen versioned dataset packages.
    
    Pattern: exports/datasets/{dataset_version}/{filename}
    Example: exports/datasets/TIV-DATASET-0001/manifest.jsonl
    """
    safe_version = sanitize_filename_component(dataset_version, "TIV-DATASET-0000")
    safe_fname = validate_storage_key(filename)
    key = f"exports/datasets/{safe_version}/{safe_fname}"
    return validate_storage_key(key)
