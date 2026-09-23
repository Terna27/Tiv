# Data Flow Architecture — Tiv AI Platform

## 1. Overview & Data Ingestion Modalities

The Tiv AI platform ingests three primary data modalities through distinct submission pipelines:
1. **Monolingual Tiv Text**
2. **Bidirectional English ↔ Tiv Translation Pairs**
3. **Spoken Tiv Audio & Accompanying Transcripts**

Each data stream progresses through defined lifecycle stages:
```
Submission Ingestion 
  ──► In-Flight Validation 
  ──► Immutable Storage & Checksum 
  ──► Automated Quality Analysis 
  ──► Database Indexing 
  ──► Human Review Queue 
  ──► Dataset Eligibility Evaluation 
  ──► Versioned Manifest Export
```

---

## 2. Ingestion Flow: Spoken Tiv Audio

Audio contributions present the highest technical complexity, requiring binary file handling, header verification, acoustic quality checks, cryptographic hashing, and dual-tier storage (raw vs. canonical derived).

### 2.1 Detailed Audio Lifecycle Flow

```mermaid
sequenceDiagram
    autonumber
    actor Contributor as Contributor (Browser)
    participant FE as Frontend UI (Dev 2)
    participant API as FastAPI Backend (Dev 1)
    participant Pipe as Data Pipeline (Dev 3)
    participant Storage as Storage Abstraction (Dev 3)
    participant DB as PostgreSQL Database (Dev 1)
    actor Reviewer as Human Reviewer (Linguist)

    Contributor->>FE: Record audio (MediaRecorder) or upload file
    Contributor->>FE: Enter transcript, select dialect, check consent
    FE->>API: POST /api/v1/submissions/audio (multipart/form-data)
    
    Note over API: Basic HTTP & Payload Validation
    API->>API: Validate contributor_id, consent == true, non-empty file
    alt Validation Fails
        API-->>FE: 400 Bad Request / 422 Unprocessable
    end

    API->>Pipe: Process Raw Audio Stream (UploadFile)
    Note over Pipe: Header Sniffing & Media Decoding
    Pipe->>Pipe: Probe container (WebM/Opus, MP4/AAC, WAV)
    Pipe->>Pipe: Compute SHA-256 Checksum
    Pipe->>Pipe: Extract technical metadata (duration, sample rate, channels)
    
    alt File Corrupt or Media Unsupported
        Pipe->>Storage: Store into quarantine/ (quarantine_key)
        Pipe-->>API: Reject with MediaValidationFailure (415/422)
        API-->>FE: Error response with technical diagnostics
    end

    Pipe->>Storage: Persist original raw file into raw/audio/{YYYY}/{MM}/{DD}/...
    Storage-->>Pipe: Return immutable storage_key_raw

    Note over Pipe: Automated Acoustic Quality Checks
    Pipe->>Pipe: Run silence detection, clipping detection, SNR estimate
    Pipe-->>API: Return ValidationResult (PASS / WARNING / FAIL) + AudioMetadata

    API->>DB: INSERT into submissions & audio_metadata (status=SUBMITTED)
    API-->>FE: 201 Created (submission_id, status=SUBMITTED, duration)

    Note over Reviewer: Human Review Workflow
    Reviewer->>API: GET /api/v1/submissions?status=SUBMITTED
    API->>Storage: Generate temporary presigned URL for playback
    API-->>Reviewer: Submission details + Presigned Audio URL + Quality Flags
    Reviewer->>API: POST /api/v1/submissions/{id}/review (decision=ACCEPTED)
    API->>DB: UPDATE submissions (status=ACCEPTED, review_notes)

    Note over Pipe: Dataset Readiness Engine
    Pipe->>DB: Evaluate dataset eligibility criteria
    alt Meets All Criteria (Consent + Valid Storage + Pass QC + Reviewer Accepted)
        DB->>DB: Set dataset_eligibility = ELIGIBLE
    else Missing Requirements
        DB->>DB: Set dataset_eligibility = INELIGIBLE (flag reasons)
    end
```

### 2.2 Audio Ingestion Stages

1. **Client Capture (`Developer 2`)**:
   - Captured in browser via `MediaRecorder` API (preferring `audio/webm;codecs=opus`, falling back to `audio/mp4` on Safari/iOS) or uploaded as pre-recorded audio file.
   - Sent as `multipart/form-data` with fields: `audio_file`, `contributor_id`, `transcript`, `dialect`, `consent`.
2. **Transport & Ingestion Gateway (`Developer 1`)**:
   - FastAPI intercepts upload via `UploadFile`.
   - Rejects unconsented submissions (`consent != true`) immediately with `400 Bad Request`.
   - Enforces preliminary file size guardrail (< 25 MB).
3. **Audio Inspection & Security Quarantine (`Developer 3`)**:
   - The raw byte stream is read in chunks to calculate a cryptographic `SHA-256` hash.
   - Media container and audio stream are parsed using binary header probes (preventing arbitrary file execution or disguised payloads).
   - If the audio header is malformed, truncated, or un-decodable, the file is moved to the `quarantine/` namespace, and an error is returned.
4. **Immutable Raw Storage (`Developer 3`)**:
   - The verified original byte stream is saved immutably into `raw/audio/{YYYY}/{MM}/{DD}/{submission_id}_{hash[:8]}.{ext}`.
   - The original file is **never modified, re-encoded, or overwritten**.
5. **Acoustic Quality Analysis (`Developer 3`)**:
   - Audio is analyzed for:
     - Minimum duration (≥ 0.5s) and maximum duration (≤ 120.0s).
     - Full file silence (peak amplitude < -60 dBFS).
     - Digital clipping percentage (> 2% clipped samples generates a `WARNING`).
     - Signal-to-Noise Ratio (SNR) estimation.
6. **Metadata & Status Persistence (`Developer 1`)**:
   - Technical metadata (codec, sample rate, channels, bit depth, duration, checksum) and initial quality status (`PASS` or `WARNING`) are written to PostgreSQL.
   - The submission status is set to `SUBMITTED`.
7. **Linguistic Review (`Developer 1 / Developer 2`)**:
   - Tiv community reviewers listen to audio using temporary private presigned URLs and compare it to the transcript and dialect.
   - Reviewer enters `decision` (`ACCEPTED`, `REJECTED`, or `NEEDS_CORRECTION`).
8. **Dataset Eligibility Gating (`Developer 3`)**:
   - Acceptance by a reviewer triggers the eligibility evaluator.
   - If the submission satisfies consent, provenance, raw storage existence, and passing quality criteria, its status transitions to `ELIGIBLE`.

---

## 3. Ingestion Flow: Monolingual Tiv Text

```mermaid
flowchart TD
    A["Contributor enters Tiv text in React UI"] --> B["Frontend validates non-empty & consent"]
    B --> C["POST /api/v1/submissions/text (JSON)"]
    C --> D["FastAPI Pydantic schema validation"]
    D --> E["Developer 3 Text Quality Checks"]
    
    subgraph TextQC ["Automated Text Quality (Dev 3)"]
        E1["Unicode NFC Normalization"]
        E2["Length check (min 3 chars, max 1000 chars)"]
        E3["Control character & script sanitation"]
        E4["Normalized hash duplicate check"]
        E1 --> E2 --> E3 --> E4
    end

    E --> TextQC
    TextQC --> F{"Quality Check Result"}
    F -- "FAIL (Empty / Gibberish)" --> G["Return 422 Unprocessable"]
    F -- "PASS / WARNING (Duplicate)" --> H["Persist to PostgreSQL (status=SUBMITTED)"]
    H --> I["Human Review Queue (Linguistic Accuracy)"]
    I --> J{"Reviewer Decision"}
    J -- "ACCEPTED" --> K["Evaluate Dataset Eligibility"]
    J -- "REJECTED" --> L["status = REJECTED"]
    J -- "NEEDS_CORRECTION" --> M["status = NEEDS_CORRECTION"]
```

### Steps:
1. **Frontend Input**: User submits `tivText`, `source`, `dialect`, and `consent`.
2. **API Schema Validation**: Pydantic validates field presence and length constraints.
3. **Normalization & Sanitization**: Text is normalized to Unicode Canonical Decomposition followed by Canonical Composition (`NFC`), stripping zero-width spaces and unprintable control characters.
4. **Duplicate Hashing**: SHA-256 of the normalized text is checked against an index of accepted texts.
5. **Persistence**: Record inserted into `submissions` and `text_submissions` tables with status `SUBMITTED`.
6. **Human Review**: Reviewer verifies that the text is authentic Tiv orthography and grammatically sound.

---

## 4. Ingestion Flow: English ↔ Tiv Translation Pairs

```mermaid
flowchart TD
    T1["Contributor inputs sourceText & targetText"] --> T2["Selects sourceLanguage & targetLanguage"]
    T2 --> T3["Confirms consent & submits form"]
    T3 --> T4["POST /api/v1/submissions/translations (JSON)"]
    T4 --> T5["Pydantic Ingestion Validation"]
    
    subgraph TransQC ["Translation QC Checks (Dev 3)"]
        Q1["Validate language pair: en->tiv OR tiv->en"]
        Q2["Verify source != target (not identical)"]
        Q3["Unicode NFC normalization on both texts"]
        Q4["Pairwise hash deduplication"]
        Q1 --> Q2 --> Q3 --> Q4
    end

    T5 --> TransQC
    TransQC --> T6{"QC Evaluation"}
    T6 -- "Invalid pair / Identical" --> T7["Return 400/422 Client Error"]
    T6 -- "PASS" --> T8["Persist to PostgreSQL (status=SUBMITTED)"]
    T8 --> T9["Bilingual Reviewer Queue"]
    T9 --> T10{"Reviewer Decision"}
    T10 -- "ACCEPTED" --> T11["Evaluate Dataset Eligibility"]
    T10 -- "REJECTED" --> T12["status = REJECTED"]
```

### Steps:
1. **Direction Validation**: Verifies that translation pair represents either `en → tiv` or `tiv → en`.
2. **Identity Guard**: Rejects submissions where `sourceText == targetText` unless flagged as a specialized loanword.
3. **Cross-language Token Checks**: Verifies non-trivial length ratio (e.g. 1 English word translated to 500 Tiv characters indicates spam/malformed data).
4. **Persistence & Triage**: Stored with metadata indicating language directions and dialect tags.
5. **Bilingual Review**: Reviewers verify translation adequacy and natural fluency.

---

## 5. Architectural Distinction: Core Artifact Concepts

To prevent architectural ambiguity between storage layers, database states, and machine learning pipelines, the platform strictly differentiates six core concepts:

| Concept | Definition | Storage Location | Mutability |
| :--- | :--- | :--- | :--- |
| **1. Raw Contribution** | The exact, unmodified byte stream submitted by the browser (WebM, MP4, WAV, raw text). | Object Store: `raw/` | **Immutable** |
| **2. Processed / Derived Artifact** | Standardized, normalized transformation (e.g. 16 kHz 16-bit mono WAV, NFC-normalized text). | Object Store: `processed/` | Reproducible / Regenerable |
| **3. Database Metadata** | Relational records capturing submission parameters, technical audio metrics, timestamps, and hashes. | PostgreSQL (`submissions`, `audio_metadata`) | Transactional |
| **4. Review State** | The human linguistic assessment (`SUBMITTED`, `UNDER_REVIEW`, `ACCEPTED`, `REJECTED`, `NEEDS_CORRECTION`). | PostgreSQL (`submissions.review_status`) | State-machine controlled |
| **5. Dataset Eligibility** | Rule-governed boolean/enum determining if a record satisfies all governance, quality, and review gates. | PostgreSQL (`submissions.dataset_eligibility`) | Deterministic Rule Evaluation |
| **6. Dataset Membership** | The inclusion of an eligible record inside a frozen, immutable versioned dataset release (e.g. `TIV-DATASET-0001`). | Object Store: `exports/` (JSONL manifests) | **Immutable** snapshot |

---

## 6. Traceability & Audit Trail Guarantee

Every downstream machine learning sample must maintain verifiable provenance back to its origin:

```
ML Sample (e.g. ASR Audio Chunk)
  └── Manifest Reference (e.g. manifest.jsonl in TIV-DATASET-0001)
        └── Submission ID (UUIDv7)
              ├── Contributor ID (Pseudonymous ID)
              ├── Consent Record (Version "v1.0", Timestamp, Consent Hash)
              ├── Raw File Checksum (SHA-256 matches raw storage object)
              ├── Quality Validation Log (Automated QC outputs)
              └── Reviewer Decision Log (Reviewer ID, Timestamp, Review Notes)
```

If an error, bias, or consent revocation occurs at any point in the lifecycle, the audit trail enables immediate surgical identification and exclusion of affected artifacts without corrupting the remainder of the corpus.
