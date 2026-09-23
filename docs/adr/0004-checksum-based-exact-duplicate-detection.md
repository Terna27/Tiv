# ADR 0004: Checksum-Based Exact Duplicate Detection for MVP

## Status
Accepted

## Context
Data collection portals are susceptible to redundant submissions: contributors may submit the same text sentence multiple times, upload duplicate audio files, or inadvertently double-click submission buttons. Identifying duplicates is essential to maintain dataset quality and prevent model overfitting.

However, advanced deduplication techniques—such as perceptual audio hashing (Chromaprint/AcoustID), deep acoustic embeddings (wav2vec2/CLAP), or fuzzy text clustering (MinHash LSH)—introduce heavy dependencies (PyTorch, FFmpeg C bindings, vector indexes) that dramatically complicate local development and slow down the initial ingestion MVP.

## Decision
For Week-1 MVP data collection:
1. **Audio Deduplication**: Use cryptographic `SHA-256` hashing computed over the raw incoming byte stream.
2. **Text Deduplication**: Use `SHA-256` hashing computed over Unicode NFC-normalized, lowercased, and punctuation-stripped text strings.
3. Duplicates will trigger a non-blocking `WARNING: POTENTIAL_DUPLICATE` flag in the review queue rather than hard HTTP rejections, allowing human reviewers to review edge cases.
4. Perceptual and neural embedding-based deduplication is documented as a post-MVP roadmap item and deferred to future milestones.

## Consequences
### Positive
- Extremely fast computation ($O(1)$ lookup via indexed hash fields in PostgreSQL).
- Zero external neural network or complex C-library runtime dependencies during Week-1.
- Keeps localhost installation lightweight and reliable across all developer workstations.

### Negative / Trade-offs
- Will not catch identical speech recorded across different file formats (e.g. same voice re-recorded or re-encoded from WebM to MP3). This limitation is acceptable for initial community crowdsourcing and will be enhanced in later milestones.
