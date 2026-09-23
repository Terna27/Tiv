# ADR 0002: Abstract Storage Provider Layer

## Status
Accepted

## Context
The platform requires audio and artifact storage across diverse development and deployment environments:
- Local development requires a zero-dependency, offline-capable setup using local disk paths (`.storage/`) so developers are not blocked by external cloud credentials, network latency, or cloud account setups.
- Staging and production deployments require secure, scalable, private S3-compatible cloud object storage (AWS S3, MinIO, Cloudflare R2, or Google Cloud Storage).
- Directly binding application code to `boto3` or `os.path` creates tight coupling, impairs testability, and prevents swapping storage providers.

## Decision
We define an abstract storage interface (`StorageBackend`) in Python that encapsulates all file and artifact operations:
- Operations include `save`, `open_read`, `exists`, `delete`, `get_metadata`, and `generate_presigned_url`.
- Implement a `LocalStorageBackend` for local development and automated CI testing.
- Implement an `S3StorageBackend` for production cloud deployments.
- Configure backend selection via environment variables (`STORAGE_BACKEND=local|s3`).
- Application and pipeline code will interact exclusively with the `StorageBackend` abstraction.

## Consequences
### Positive
- Developers 1, 2, and 3 can develop and test the entire platform locally without cloud dependencies.
- Zero vendor lock-in: migration between AWS S3, Cloudflare R2, or self-hosted MinIO requires zero application code changes.
- Seamless unit testing using mock or filesystem-backed storage.

### Negative / Trade-offs
- Requires implementing and maintaining two backend adapters (`local` and `s3`).
- Local presigned URL simulation requires a lightweight streaming proxy endpoint in the local FastAPI backend.
