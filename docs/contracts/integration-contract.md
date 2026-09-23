# Developer Integration Contract Summary

## 1. Purpose & High-Level Integration Map

This document serves as the single source of truth across all three engineering roles for Milestone 0 and subsequent implementation milestones. It traces every contribution from the contributor's browser, through the FastAPI backend and data pipeline, into PostgreSQL and storage, through the reviewer queue, and into dataset eligibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. WHAT DEVELOPER 2 SENDS (Frontend Client)                                 │
│    - JSON for text & translation; multipart/form-data for audio             │
│    - Form fields, consent boolean, transcripts, dialect selections          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. WHAT DEVELOPER 1 ACCEPTS (FastAPI & Pydantic Gateway)                    │
│    - Validates presence, types, authentication/session, and consent == true │
│    - Delegates media bytes & quality evaluation to Developer 3 services     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. WHAT DEVELOPER 3 VALIDATES & PROCESSES (Data Pipeline & Storage)         │
│    - Probes binary headers, validates duration/codecs, computes SHA-256     │
│    - Runs acoustic/text QC checks, writes immutable raw storage artifact    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. WHAT IS STORED (PostgreSQL & Object Storage)                             │
│    - Postgres: Relational records, technical metrics, QC status, hashes     │
│    - Storage: raw/audio/... (immutable original byte stream)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. WHAT THE REVIEWER SEES (Review Dashboard UI)                             │
│    - Text/translation preview, dialect, audio playback via presigned URL    │
│    - Quality flags & warnings (e.g. "Low volume", "Potential duplicate")   │
│    - Decision actions: [Accept], [Reject], [Needs Correction]               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. WHAT BECOMES DATASET ELIGIBLE (ML-Ready Corpus)                          │
│    - Records satisfying: ACCEPTED + Valid Consent + Valid Storage + QC PASS │
│    - Rendered into immutable versioned releases (e.g. TIV-DATASET-0001)     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Workflow Breakdown by Modality

### 2.1 Spoken Tiv Audio

| Stage | Action & Specifications | Responsible Role |
| :--- | :--- | :--- |
| **Developer 2 Sends** | `POST /api/v1/submissions/audio` (`multipart/form-data`)<br>• `audio_file`: Binary Blob (`recording.webm` or `.m4a`)<br>• `contributor_id`: `"contrib_01h8..."`<br>• `transcript`: `"M ngu lamen zwa Tiv sha gbashima."`<br>• `dialect`: `"Central Tiv"`<br>• `consent`: `true` | Developer 2 |
| **Developer 1 Accepts** | FastAPI route checks `consent == true` and verifies `UploadFile` presence. Injects `Developer3.AudioPipelineService`. | Developer 1 |
| **Developer 3 Validates** | • Probes container magic bytes (rejects non-audio with `415`)<br>• Decodes duration (rejects `< 0.5s` or `> 120s` with `422`)<br>• Computes SHA-256 hash<br>• Detects silence and clipping<br>• Writes stream to `raw/audio/{YYYY}/{MM}/{DD}/{sub_id}_{hash[:8]}.{ext}` | Developer 3 |
| **What is Stored** | • **Storage**: Original file preserved in `raw/`<br>• **PostgreSQL**: `submissions` record (`status='SUBMITTED'`, `quality_status='PASS'`), `audio_metadata` record (sample rate, channels, codec, duration, SHA-256) | Developer 1 & 3 |
| **What Reviewer Sees** | • Audio playback player (backed by 15-minute presigned GET URL)<br>• Spoken transcript vs. playback<br>• Dialect badge<br>• Action buttons: [Accept], [Reject], [Needs Correction] | Developer 2 & 1 |
| **What Becomes Eligible** | When reviewer clicks [Accept], Dev 3's eligibility check runs. If consent is valid, raw file exists, and quality passed, item becomes `ELIGIBLE` for inclusion in `TIV-DATASET-XXXX`. | Developer 3 |

### 2.2 Monolingual Tiv Text

| Stage | Action & Specifications | Responsible Role |
| :--- | :--- | :--- |
| **Developer 2 Sends** | `POST /api/v1/submissions/text` (`application/json`)<br>• `contributorId`: `"contrib_01h8..."`<br>• `tivText`: `"Kwagh hemba a hemba ze."`<br>• `source`: `"proverb"`<br>• `dialect`: `"Central Tiv"`<br>• `consent`: `true` | Developer 2 |
| **Developer 1 Accepts** | Pydantic schema validation: checks types, non-empty text, and consent. | Developer 1 |
| **Developer 3 Validates** | • Unicode NFC normalization<br>• Length check (3 – 1000 characters)<br>• Malformed character / spam check<br>• SHA-256 duplicate detection against existing texts | Developer 3 |
| **What is Stored** | PostgreSQL `submissions` row with `type='text'` and normalized text record. | Developer 1 |
| **What Reviewer Sees** | Review dashboard displays Tiv sentence, dialect, source context, and duplicate warnings. | Developer 2 & 1 |
| **What Becomes Eligible** | Items with `review_status='ACCEPTED'`, `consent=true`, and no blocking duplicate flags become `dataset_eligibility='ELIGIBLE'`. | Developer 3 |

### 2.3 English ↔ Tiv Translation

| Stage | Action & Specifications | Responsible Role |
| :--- | :--- | :--- |
| **Developer 2 Sends** | `POST /api/v1/submissions/translations` (`application/json`)<br>• `contributorId`: `"contrib_01h8..."`<br>• `sourceText`: `"Where are you going?"`<br>• `targetText`: `"U ngu yemen hana?"`<br>• `sourceLanguage`: `"en"`, `targetLanguage`: `"tiv"`<br>• `dialect`: `"Central Tiv"`, `consent`: `true` | Developer 2 |
| **Developer 1 Accepts** | Validates language pair codes (`en` & `tiv`), non-empty strings, and consent. | Developer 1 |
| **Developer 3 Validates** | • Verifies `sourceText != targetText`<br>• Checks reasonable token length ratio (flags anomalous length imbalances)<br>• Pairwise duplicate hashing | Developer 3 |
| **What is Stored** | PostgreSQL `submissions` row with `type='translation'`, source text, target text, and language codes. | Developer 1 |
| **What Reviewer Sees** | Side-by-side translation comparison card with direction badges (`EN → TIV`). | Developer 2 & 1 |
| **What Becomes Eligible** | Items marked `ACCEPTED` by bilingual reviewer transition to `dataset_eligibility='ELIGIBLE'`. | Developer 3 |

---

## 3. Explicit Ambiguity Resolutions

1. **Audio Field Naming**:
   - *Ambiguity*: In `src/api/client.js`, `submitAudio` uses `form.append("contributor_id", ...)` and `form.append("audio_file", ...)`, but text endpoints use camelCase (`contributorId`).
   - *Resolution*: Audio multipart endpoint strictly uses `snake_case` (`audio_file`, `contributor_id`, `transcript`, `dialect`, `consent`). Developer 1 will add an alias in Pydantic so either casing is parsed without error.
2. **Hardcoded WebM Filename in Frontend**:
   - *Ambiguity*: In `client.js`, Developer 2 writes `form.append("audio_file", audioBlob, "recording.webm")`, even on Safari where the blob is AAC/MP4.
   - *Resolution*: Developer 1 and Developer 3 will ignore the client-sent filename for MIME detection and determine the true format via magic bytes and binary header inspection.
3. **Reviewer Acceptance vs. Dataset Inclusion**:
   - *Ambiguity*: Does an "ACCEPTED" status mean the data is now part of the AI dataset?
   - *Resolution*: No. Reviewer acceptance sets `review_status = "ACCEPTED"`. The automated eligibility engine then independently confirms consent, storage presence, and passing QC before setting `dataset_eligibility = "ELIGIBLE"`.
4. **Playback Security**:
   - *Ambiguity*: How does the reviewer listen to audio stored on the backend?
   - *Resolution*: `GET /api/v1/submissions/{id}` returns a transient `audio_playback_url`. In local dev, this is a local proxy URL (`/api/v1/media/...`). In production, this is an S3 presigned URL expiring in 15 minutes. No public bucket access is permitted.
