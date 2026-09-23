# Metadata Contract & Provenance Schema

## 1. Metadata Categorization & Architecture

To prevent data corruption, preserve linguistic integrity, and ensure complete provenance, all metadata in the Tiv AI platform is strictly partitioned into four functional domains:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Contribution Metadata (Linguistic & Submission Context)  │
├─────────────────────────────────────────────────────────────┤
│ 2. Audio Technical Metadata (Acoustic & Container Metrics)  │
├─────────────────────────────────────────────────────────────┤
│ 3. Speaker / Demographic Metadata (Acoustic Stratification) │
├─────────────────────────────────────────────────────────────┤
│ 4. Governance & Audit Metadata (Consent, QC & Review Gates) │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Metadata Field Specifications

### 2.1 Category 1: Contribution Metadata

Captures the core linguistic attributes of the submission.

| Field Name | Type | Status | Description / Allowed Values |
| :--- | :--- | :--- | :--- |
| `submission_id` | String | **Required** | Canonical system UUIDv7 or prefixed identifier (e.g., `sub_01h8...`). |
| `contributor_id` | String | **Required** | Pseudonymous identifier of the contributor (`contrib_01h8...`). |
| `contribution_type`| Enum | **Required** | `"text"`, `"translation"`, or `"audio"`. |
| `created_at` | Timestamp | **Required** | ISO 8601 UTC timestamp of submission creation. |
| `language` | String | **Required** | Primary language tag (ISO 639-3: `"tiv"`). |
| `dialect` | Enum / String | Optional | Dialect tag: `"Central Tiv"`, `"Eastern Tiv"`, `"Western Tiv"`, `"Other"`, or `"Not sure"`. |
| `source` | String | Optional | Origin context: `"everyday conversation"`, `"proverb"`, `"literature"`, `"news"`, `"spontaneous"`. |

### 2.2 Category 2: Audio Technical Metadata

Extracted server-side by Developer 3's media probe during binary inspection.

| Field Name | Type | Status | Description / Allowed Values |
| :--- | :--- | :--- | :--- |
| `original_filename`| String | Informational| Client-reported filename (e.g. `recording.webm`). Treated strictly as informational metadata. |
| `storage_key_raw` | String | **Required** | Authoritative immutable object storage path (e.g. `raw/audio/2026/09/23/...`). |
| `storage_key_processed`| String| Optional | Path to canonical derived artifact (e.g. `processed/audio/...16k_mono.wav`). |
| `container_format` | String | **Required** | Verified container: `"webm"`, `"ogg"`, `"mp4"`, `"wav"`, `"mp3"`. |
| `codec` | String | **Required** | Verified audio stream codec: `"opus"`, `"aac"`, `"pcm_s16le"`, `"mp3"`. |
| `duration_seconds` | Float | **Required** | Exact decoded duration in seconds (precision to 3 decimal places). |
| `sample_rate_hz` | Integer | **Required** | Audio sampling rate in Hertz (e.g. `16000`, `44100`, `48000`). |
| `channels` | Integer | **Required** | Number of audio channels (`1` for mono, `2` for stereo). |
| `bit_depth` | Integer | Optional | Bit depth where applicable (e.g. `16` or `24` for PCM; `null` for lossy codecs). |
| `file_size_bytes` | Integer | **Required** | Exact byte length of the uploaded file. |
| `checksum_sha256` | String | **Required** | 64-character lowercase hexadecimal SHA-256 hash of the raw file. |

### 2.3 Category 3: Speaker & Demographic Metadata

Strictly minimized to avoid gathering personally identifying information (PII). Collected optionally solely to support dialectal diversity and acoustic balance in future ASR/TTS training datasets.

| Field Name | Type | Status | Description / Allowed Values |
| :--- | :--- | :--- | :--- |
| `age_range` | String | Optional | Age bracket: `"18-25"`, `"26-40"`, `"41-60"`, `"60+"`. |
| `gender` | String | Optional | Gender identity: `"male"`, `"female"`, `"non-binary"`, `"prefer_not_to_say"`. |
| `region` | String | Optional | Geographic location / LGA (e.g., `"Gboko"`, `"Makurdi"`, `"Vandeikya"`, `"Diaspora"`). |
| `speaker_type` | String | Optional | Speaker background: `"native"`, `"fluent_l2"`, `"learner"`. |
| `recording_environment`| String| Optional | Environment tag: `"quiet_room"`, `"office"`, `"outdoor"`, `"noisy"`. |

> **DATA PRIVACY MANDATE**:
> Names, email addresses, phone numbers, home addresses, IP addresses, and device identifiers must **never** be included in exportable dataset metadata.

### 2.4 Category 4: Governance & Provenance Metadata

Ensures legal compliance, tracking of human reviews, and automated dataset eligibility.

| Field Name | Type | Status | Description / Allowed Values |
| :--- | :--- | :--- | :--- |
| `consent_status` | Boolean | **Required** | Must be `true` for submission to be retained. |
| `consent_version` | String | **Required** | Version tag of the consented terms (e.g., `"v1.0-2026-09"`). |
| `consent_timestamp` | Timestamp | **Required** | Precise ISO 8601 UTC timestamp when consent was confirmed. |
| `client_user_agent` | String | Optional | Anonymized user agent string for debugging browser audio quirks. |
| `review_status` | Enum | **Required** | `"SUBMITTED"`, `"UNDER_REVIEW"`, `"ACCEPTED"`, `"REJECTED"`, `"NEEDS_CORRECTION"`. |
| `review_notes` | String | Optional | Reviewer feedback or justification for rejection/correction. |
| `reviewed_by` | String | Optional | Pseudonymous reviewer ID. |
| `reviewed_at` | Timestamp | Optional | ISO 8601 UTC timestamp of review decision. |
| `quality_status` | Enum | **Required** | Automated QC assessment: `"PASS"`, `"WARNING"`, `"FAIL"`. |
| `quality_report` | JSON | Optional | Detailed metrics: silence ratio, clipping percentage, SNR estimate. |
| `dataset_eligibility`| Enum | **Required** | `"PENDING_REVIEW"`, `"ELIGIBLE"`, `"INELIGIBLE"`, `"EXCLUDED_BY_WITHDRAWAL"`. |

---

## 3. Database Schema Blueprint (PostgreSQL / SQLAlchemy)

For Developer 1's implementation with SQLAlchemy and Alembic, the metadata maps to the following relational structure:

```sql
-- Core submissions table
CREATE TABLE submissions (
    id VARCHAR(36) PRIMARY KEY,
    contributor_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL,            -- 'text', 'translation', 'audio'
    dialect VARCHAR(50),
    source VARCHAR(255),
    consent_status BOOLEAN NOT NULL DEFAULT TRUE,
    consent_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    consent_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_status VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    reviewed_by VARCHAR(36),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    quality_report JSONB,
    dataset_eligibility VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audio technical metadata table (1:1 with audio submissions)
CREATE TABLE audio_metadata (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL UNIQUE REFERENCES submissions(id) ON DELETE CASCADE,
    storage_key_raw VARCHAR(512) NOT NULL,
    storage_key_processed VARCHAR(512),
    original_filename VARCHAR(255),
    container_format VARCHAR(30) NOT NULL,
    codec VARCHAR(30) NOT NULL,
    duration_seconds NUMERIC(8, 3) NOT NULL,
    sample_rate_hz INTEGER NOT NULL,
    channels SMALLINT NOT NULL,
    bit_depth SMALLINT,
    file_size_bytes BIGINT NOT NULL,
    checksum_sha256 CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexing for rapid triage and eligibility queries
CREATE INDEX idx_submissions_type_status ON submissions(type, review_status);
CREATE INDEX idx_submissions_eligibility ON submissions(dataset_eligibility);
CREATE INDEX idx_audio_checksum ON audio_metadata(checksum_sha256);
```
