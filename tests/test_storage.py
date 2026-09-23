"""Unit test suite for the Tiv AI Storage Abstraction Layer (Milestone 2)."""

import io
import pytest
from pathlib import Path

from app.storage.base import StorageBackend
from app.storage.exceptions import (
    InvalidStorageKeyError,
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
    PathTraversalError,
    StorageWriteError,
)
from app.storage.keys import (
    generate_export_key,
    generate_processed_audio_key,
    generate_quarantine_key,
    generate_raw_audio_key,
    validate_storage_key,
)
from app.storage.local import LocalStorageBackend
from app.storage.models import StoredObject
from app.storage.service import get_storage, reset_storage, set_storage_override


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageBackend:
    """Fixture providing an isolated LocalStorageBackend rooted in a pytest tmp_path."""
    return LocalStorageBackend(root_dir=tmp_path / "storage_root")


def test_save_and_read_bytes(storage: LocalStorageBackend):
    """Test saving raw bytes and reading them back verbatim."""
    key = "raw/audio/2026/09/23/test_01.bin"
    payload = b"RIFF-TIV-TEST-AUDIO-PAYLOAD-12345"

    obj = storage.save(key, payload, content_type="audio/wav")

    assert isinstance(obj, StoredObject)
    assert obj.key == key
    assert obj.size_bytes == len(payload)
    assert obj.content_type == "audio/wav"
    assert len(obj.checksum_sha256) == 64

    # Verify read_bytes returns exact payload
    read_data = storage.read_bytes(key)
    assert read_data == payload


def test_save_from_stream(storage: LocalStorageBackend):
    """Test streaming upload from an open binary file-like object."""
    key = "processed/audio/2026/09/stream_test.wav"
    payload = b"PCM_AUDIO_DATA_" * 1024  # ~15 KB
    stream = io.BytesIO(payload)

    obj = storage.save(key, stream, content_type="audio/wav")

    assert obj.size_bytes == len(payload)
    assert storage.read_bytes(key) == payload


def test_stream_chunks(storage: LocalStorageBackend):
    """Test chunked streaming from storage without full RAM buffering."""
    key = "processed/audio/2026/09/chunk_test.wav"
    payload = b"CHUNK_ABC_" * 5000
    storage.save(key, payload)

    collected = b""
    for chunk in storage.stream(key, chunk_size=1024):
        collected += chunk

    assert collected == payload


def test_exists_query(storage: LocalStorageBackend):
    """Test exists() accurately reflects file presence."""
    key = "raw/audio/2026/09/23/exists_check.webm"
    assert storage.exists(key) is False

    storage.save(key, b"webm_data")
    assert storage.exists(key) is True


def test_metadata_retrieval(storage: LocalStorageBackend):
    """Test stored metadata matches stored object properties and custom metadata."""
    key = "processed/audio/2026/09/meta_check.wav"
    payload = b"SAMPLE_METADATA_VERIFICATION"
    custom_meta = {"contributor_id": "contrib_123", "dialect": "Central Tiv"}

    saved_obj = storage.save(key, payload, content_type="audio/wav", metadata=custom_meta)
    fetched_obj = storage.get_metadata(key)

    assert fetched_obj.key == saved_obj.key
    assert fetched_obj.size_bytes == len(payload)
    assert fetched_obj.checksum_sha256 == saved_obj.checksum_sha256
    assert fetched_obj.content_type == "audio/wav"
    assert fetched_obj.custom_metadata == custom_meta


def test_delete_object(storage: LocalStorageBackend):
    """Test deleting an object removes both file and companion metadata."""
    key = "quarantine/2026/09/corrupt_upload.bin"
    storage.save(key, b"malformed")

    assert storage.exists(key) is True
    deleted = storage.delete(key)
    assert deleted is True
    assert storage.exists(key) is False

    # Deleting again must raise ObjectNotFoundError
    with pytest.raises(ObjectNotFoundError):
        storage.delete(key)


def test_read_missing_object(storage: LocalStorageBackend):
    """Test reading non-existent key raises ObjectNotFoundError."""
    with pytest.raises(ObjectNotFoundError):
        storage.read_bytes("raw/audio/missing.webm")

    with pytest.raises(ObjectNotFoundError):
        storage.open_read("raw/audio/missing.webm")

    with pytest.raises(ObjectNotFoundError):
        storage.get_metadata("raw/audio/missing.webm")


def test_immutability_in_raw_namespace(storage: LocalStorageBackend):
    """Test that objects in raw/ namespace cannot be overwritten even if overwrite=True."""
    key = "raw/audio/2026/09/23/original.webm"
    storage.save(key, b"first_version")

    # Attempting to save again without overwrite
    with pytest.raises(ObjectAlreadyExistsError):
        storage.save(key, b"second_version", overwrite=False)

    # Attempting to save again WITH overwrite=True must STILL be rejected in raw/
    with pytest.raises(ObjectAlreadyExistsError):
        storage.save(key, b"second_version", overwrite=True)

    # Verify original bytes remain unmodified
    assert storage.read_bytes(key) == b"first_version"


def test_overwrite_permitted_in_non_raw_namespace(storage: LocalStorageBackend):
    """Test that derived/processed objects allow overwrite when explicitly requested."""
    key = "processed/audio/2026/09/derived.wav"
    storage.save(key, b"v1_data")

    # Without overwrite flag, raises ObjectAlreadyExistsError
    with pytest.raises(ObjectAlreadyExistsError):
        storage.save(key, b"v2_data", overwrite=False)

    # With overwrite=True, succeeds for non-raw namespaces
    obj_v2 = storage.save(key, b"v2_data", overwrite=True)
    assert storage.read_bytes(key) == b"v2_data"
    assert obj_v2.size_bytes == len(b"v2_data")


def test_nested_path_creation(storage: LocalStorageBackend):
    """Test that nested parent directories are created automatically."""
    deep_key = "raw/audio/2026/12/31/deep/nested/item.bin"
    storage.save(deep_key, b"nested_content")

    assert storage.exists(deep_key) is True
    assert storage.read_bytes(deep_key) == b"nested_content"


def test_path_traversal_prevention(storage: LocalStorageBackend):
    """Test that malicious path traversal attempts are detected and rejected."""
    traversal_keys = [
        "../secret.txt",
        "../../etc/passwd",
        "/absolute/path/file.wav",
        "raw/../../../secret.txt",
        "raw/./test.wav",
        "raw/audio/../../escaped.bin",
    ]

    for malicious_key in traversal_keys:
        with pytest.raises((PathTraversalError, InvalidStorageKeyError)):
            storage.save(malicious_key, b"exploit")

        with pytest.raises((PathTraversalError, InvalidStorageKeyError)):
            storage.read_bytes(malicious_key)


def test_invalid_key_characters(storage: LocalStorageBackend):
    """Test that keys with null bytes or backslashes are rejected."""
    invalid_keys = [
        "raw/audio/test\x00file.wav",
        "raw\\audio\\windows_style.wav",
        "",
    ]
    for key in invalid_keys:
        with pytest.raises(InvalidStorageKeyError):
            validate_storage_key(key)


def test_atomic_write_failure_cleanup(storage: LocalStorageBackend):
    """Test that interrupted writes do not leave incomplete files at the target path."""
    key = "raw/audio/2026/09/23/failing_upload.bin"

    class FailingStream(io.BytesIO):
        def read(self, size=-1):
            raise IOError("Simulated network disconnection during upload")

    failing_stream = FailingStream(b"partial_data")

    with pytest.raises(StorageWriteError):
        storage.save(key, failing_stream)

    # Target path must not exist
    assert storage.exists(key) is False

    # Staging temp directory must not contain leftover files
    tmp_files = list(storage.tmp_path.glob("tmp_upload_*"))
    assert len(tmp_files) == 0


def test_key_generators():
    """Test safe key generators produce valid, date-partitioned storage keys."""
    raw_key = generate_raw_audio_key("sub_01h8q7j4", "a1b2c3d4e5f6", "webm")
    assert raw_key.startswith("raw/audio/")
    assert "sub_01h8q7j4_a1b2c3d4.webm" in raw_key

    proc_key = generate_processed_audio_key("sub_01h8q7j4", tag="16k_mono")
    assert proc_key.startswith("processed/audio/")
    assert "sub_01h8q7j4_16k_mono.wav" in proc_key

    quar_key = generate_quarantine_key("q_999", reason="truncated_header")
    assert quar_key.startswith("quarantine/")
    assert "q_999_truncated_header.bin" in quar_key

    exp_key = generate_export_key("TIV-DATASET-0001", "manifest.jsonl")
    assert exp_key == "exports/datasets/TIV-DATASET-0001/manifest.jsonl"


def test_storage_factory(tmp_path: Path):
    """Test central get_storage() factory and test isolation overrides."""
    reset_storage()
    custom_backend = LocalStorageBackend(root_dir=tmp_path / "custom")
    set_storage_override(custom_backend)

    active_storage = get_storage()
    assert isinstance(active_storage, StorageBackend)
    assert active_storage.root_path == (tmp_path / "custom").resolve()

    reset_storage()
