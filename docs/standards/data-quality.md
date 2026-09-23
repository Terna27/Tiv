# Data Quality & Automated Validation Standard

## 1. Principles & Quality Philosophy

1. **Automated Guards Complement, Never Replace, Human Review**: Automated checks catch binary corruption, acoustic defects, trivial spam, and duplicate submissions. They cannot evaluate idiomatic nuances or cultural authenticity.
2. **Deterministic Grading**: Automated checks yield one of three discrete outcomes:
   - `PASS`: All technical criteria satisfied; clear for human review.
   - `WARNING`: Sub-optimal or suspicious attributes detected (e.g. potential duplicate, mild noise). Item proceeds to review queue with informative warning tags.
   - `FAIL`: Fatal structural flaw (e.g. 0-byte file, un-decodable audio, pure silence, empty text). Item is blocked from human review and disqualified from dataset eligibility.
3. **Reproducibility**: All quality rules, thresholds, and outputs are versioned (`quality_policy_version = "v1.0"`).

---

## 2. Text Quality Specifications

Automated validation applied to monolingual Tiv text contributions:

| Rule Code | Check Description | Criteria | Result | Action |
| :--- | :--- | :--- | :--- | :--- |
| `TXT_EMPTY` | Non-empty text | Stripped length == 0 | **FAIL** | Reject HTTP request (400) |
| `TXT_MIN_LEN` | Minimum length | Stripped character count < 3 | **FAIL** | Reject HTTP request (422) |
| `TXT_MAX_LEN` | Maximum length | Stripped character count > 1,000 | **FAIL** | Reject HTTP request (422) |
| `TXT_UNICODE` | Unicode Normalization | Normalize to Unicode `NFC` | **PASS** | Auto-normalized in pipeline |
| `TXT_CONTROL` | Control characters | Disallow unprintable characters (except `\n`, `\t`) | **FAIL** | Reject or strip control bytes |
| `TXT_REPEATED`| Gibberish / Repetition | Single character repeated > 5 times (e.g. "aaaaaa") | **WARNING** | Flag for reviewer inspection |
| `TXT_DUP_EXACT`| Exact Duplicate | Normalized SHA-256 matches existing accepted text | **WARNING** | Flag as "Potential Duplicate" in review queue |

---

## 3. Translation Pair Quality Specifications

Automated validation applied to English ↔ Tiv translation contributions:

| Rule Code | Check Description | Criteria | Result | Action |
| :--- | :--- | :--- | :--- | :--- |
| `TRN_MISSING` | Source or Target Empty | `len(source.strip()) == 0` or `len(target.strip()) == 0` | **FAIL** | Reject HTTP request (400) |
| `TRN_LANG_DIR` | Direction Validity | Source and Target languages must be `en` and `tiv` (or `tiv` and `en`) | **FAIL** | Reject HTTP request (400) |
| `TRN_IDENTITY` | Non-identical texts | Normalized `sourceText == targetText` | **WARNING / FAIL** | Flag or reject unless marked as loanword |
| `TRN_RATIO` | Word Count Ratio | Length ratio between source and target > 4.0 or < 0.25 | **WARNING** | Flag for reviewer inspection |
| `TRN_DUP_PAIR` | Duplicate Pair | Pairwise normalized hash matches existing pair | **WARNING** | Flag as duplicate in review UI |

---

## 4. Audio Quality Specifications

Automated validation applied to voice submissions:

| Rule Code | Check Description | Criteria | Result | Action |
| :--- | :--- | :--- | :--- | :--- |
| `AUD_EXISTS` | File presence | Binary stream length > 0 | **FAIL** | Reject HTTP request (400) |
| `AUD_MIN_SIZE` | Minimum file size | File size < 1,024 bytes (1 KB) | **FAIL** | Reject HTTP request (422) |
| `AUD_MAX_SIZE` | Maximum file size | File size > 26,214,400 bytes (25 MB) | **FAIL** | Reject HTTP request (413) |
| `AUD_CONTAINER`| Container Magic Bytes | Recognizable EBML/WebM, RIFF/WAV, MP4, or MP3 header | **FAIL** | Quarantine file & reject (415) |
| `AUD_DECODE` | Frame Decodability | Audio frames can be read without parser exception | **FAIL** | Quarantine file & reject (422) |
| `AUD_MIN_DUR` | Minimum duration | Decoded duration < 0.5 seconds | **FAIL** | Reject HTTP request (422) |
| `AUD_MAX_DUR` | Maximum duration | Decoded duration > 120.0 seconds | **FAIL** | Reject HTTP request (422) |
| `AUD_SILENCE_ABS`| Dead Silence | Peak amplitude < -60 dBFS across entire file | **FAIL** | Reject HTTP request (422) |
| `AUD_SILENCE_REL`| Excessive Silence | Silent frames exceed 75% of duration | **WARNING** | Flag in review queue |
| `AUD_CLIPPING` | Digital Clipping | Clipped samples at 0 dBFS > 2.0% | **WARNING** | Flag in review queue |
| `AUD_DUP_EXACT`| Exact Audio Duplicate | SHA-256 matches existing audio checksum | **WARNING** | Flag duplicate in review queue |

---

## 5. Deduplication Strategy (Week-1 MVP vs Future Roadmap)

### 5.1 Week-1 Strategy (Deterministic & Fast)

1. **Text Deduplication**:
   - Normalize string: Unicode NFC, lowercase, collapse multiple whitespaces, remove terminal punctuation.
   - Hash generation: `text_hash = SHA256(normalized_text)`.
   - Indexing: Unique B-tree index in PostgreSQL on `text_hash`.
2. **Audio Exact Duplicate Detection**:
   - Compute `file_checksum = SHA256(raw_bytes)` as the stream is ingested.
   - Indexing: B-tree index on `audio_metadata.checksum_sha256`.
   - Action: If an exact matching checksum exists in the database, the submission is accepted but flagged with a `WARNING: EXACT_AUDIO_DUPLICATE` to alert reviewers that the file has already been submitted.

### 5.2 Future Enhancement Strategy (Post-MVP Roadmap)

- **Acoustic Perceptual Hashing**: Implement Chromaprint / AcoustID to detect the same audio encoded in different containers (e.g. WebM vs WAV).
- **Audio Embedding Similarity**: Extract audio embeddings using a pre-trained feature extractor (e.g. wav2vec2 or CLAP) to detect identical speech re-recorded or re-uploaded.
- **Fuzzy Text Matching**: Implement Levenshtein distance and MinHash LSH to cluster near-identical sentences.
- **Explicit Mandate**: These advanced ML-based similarity algorithms are **strictly deferred** to future milestones to preserve simplicity and avoid heavy dependencies during initial data collection.
