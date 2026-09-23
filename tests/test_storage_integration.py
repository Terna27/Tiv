"""Integration test demonstrating Application -> Storage Interface -> LocalStorage lifecycle."""

from pathlib import Path
import pytest

from app.storage import (
    StorageBackend,
    StoredObject,
    LocalStorageBackend,
    get_storage,
    set_storage_override,
    reset_storage,
    generate_raw_audio_key,
    ObjectNotFoundError,
)


def test_storage_lifecycle_integration(tmp_path: Path):
    """End-to-end integration test proving the storage abstraction contract.
    
    Verifies the complete lifecycle:
    save -> exists -> read -> metadata -> delete -> not exists
    """
    # 1. Setup isolated storage environment for integration test
    test_root = tmp_path / "integration_storage"
    backend = LocalStorageBackend(root_dir=test_root)
    set_storage_override(backend)

    try:
        # Application obtains storage purely through the abstract service interface
        storage: StorageBackend = get_storage()

        # 2. Key Generation
        submission_id = "sub_integration_01"
        payload = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00"
        key = generate_raw_audio_key(submission_id, "abcdef123456", "wav")

        # 3. Save operation
        stored: StoredObject = storage.save(
            key=key,
            data=payload,
            content_type="audio/wav",
            metadata={"source": "integration_test", "contributor": "contrib_test_99"},
        )
        assert stored.key == key
        assert stored.size_bytes == len(payload)
        assert len(stored.checksum_sha256) == 64

        # 4. Exists check
        assert storage.exists(key) is True

        # 5. Read check
        retrieved_bytes = storage.read_bytes(key)
        assert retrieved_bytes == payload

        # 6. Metadata check
        metadata = storage.get_metadata(key)
        assert metadata.size_bytes == len(payload)
        assert metadata.checksum_sha256 == stored.checksum_sha256
        assert metadata.custom_metadata["source"] == "integration_test"

        # 7. Delete check (quarantine cleanup / erasure protocol)
        assert storage.delete(key) is True

        # 8. Not exists check
        assert storage.exists(key) is False
        with pytest.raises(ObjectNotFoundError):
            storage.read_bytes(key)

    finally:
        reset_storage()
