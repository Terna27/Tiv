# Dataset Lifecycle & Future ML Interfaces — Tiv AI Platform

## 1. Overview & Separation of Concerns

A fundamental architectural principle of the Tiv AI platform is the **strict separation between Reviewer Acceptance and Dataset Eligibility**:

```
[ Contributor Submission ]
           │
           ▼
[ Automated Quality Checks ]  ──► (PASS / WARNING / FAIL)
           │
           ▼
[ Human Linguistic Review ]  ──► (ACCEPTED / REJECTED / NEEDS_CORRECTION)
           │
           ▼
[ Dataset Eligibility Evaluator ] ──► (ELIGIBLE / INELIGIBLE)
           │
           ▼
[ Immutable Dataset Snapshot ] ──► (e.g. TIV-DATASET-0001)
           │
           ▼
[ Future ML Training Splits ] ──► (ASR / MT / Chat / TTS)
```

Human reviewers evaluate linguistic authenticity, natural phrasing, and transcript alignment. They cannot be expected to inspect container bitrates, verify SHA-256 binary integrity, validate consent version hashes, or check signal-to-noise ratios. Conversely, automated checks verify technical audio health and cryptographic integrity, but cannot judge whether a Tiv proverb is accurately translated.

Therefore, **an accepted submission does NOT automatically enter a training dataset.** It must independently satisfy the automated **Dataset Eligibility Gating Criteria**.

---

## 2. Dataset Eligibility Rules Engine

A submission transitions to `dataset_eligibility = ELIGIBLE` if and only if **all** of the following predicates evaluate to `TRUE`:

```python
def evaluate_dataset_eligibility(submission: SubmissionRecord) -> EligibilityResult:
    """Deterministic evaluation of dataset readiness."""
    
    # 1. Human Review Gate
    if submission.review_status != "ACCEPTED":
        return EligibilityResult(eligible=False, reason="Awaiting human reviewer acceptance")

    # 2. Consent Gate
    if not submission.consent_status or submission.consent_withdrawn:
        return EligibilityResult(eligible=False, reason="Consent not granted or revoked")
    
    # 3. Provenance & Attribution Gate
    if not submission.contributor_id or not submission.created_at:
        return EligibilityResult(eligible=False, reason="Incomplete provenance records")

    # 4. Storage Artifact Gate (for Audio submissions)
    if submission.type == "audio":
        if not submission.storage_key_raw or not storage_backend.exists(submission.storage_key_raw):
            return EligibilityResult(eligible=False, reason="Raw storage artifact not found")
        if not submission.checksum_sha256:
            return EligibilityResult(eligible=False, reason="Missing cryptographic checksum")

    # 5. Automated Quality Gate
    if submission.quality_status == "FAIL":
        return EligibilityResult(eligible=False, reason="Blocking quality check failure")

    # All gates cleared
    return EligibilityResult(eligible=True, reason="All eligibility criteria satisfied")
```

### Eligibility States:
- `PENDING_REVIEW`: Awaiting human review decision.
- `ELIGIBLE`: Passed human review and all automated technical, storage, and consent gates.
- `INELIGIBLE`: Failed one or more technical quality checks, missing audio artifact, or rejected by reviewer.
- `EXCLUDED_BY_WITHDRAWAL`: Withdrawn by contributor after prior consent.

---

## 3. Dataset Versioning Specification

Datasets are published as immutable, versioned research and training packages. The platform adopts a sequential versioning convention:

```
TIV-DATASET-XXXX
```
- Examples: `TIV-DATASET-0001`, `TIV-DATASET-0002`

### 3.1 Dataset Snapshot Bundle Structure
Each dataset version is frozen in the `exports/datasets/{version}/` storage namespace:

```
exports/datasets/TIV-DATASET-0001/
├── dataset_manifest.json          # High-level dataset metadata & summary statistics
├── data_text.jsonl                # Monolingual Tiv text records
├── data_translations.jsonl        # English <-> Tiv parallel translation records
├── data_speech.jsonl              # Spoken Tiv audio records & transcripts
├── checksums.sha256               # Cryptographic hashes of all constituent files
└── audio/                         # Standardized canonical 16kHz mono audio files
    ├── sub_01h8q7j4_16k_mono.wav
    └── ...
```

### 3.2 Dataset Metadata Schema (`dataset_manifest.json`)
```json
{
  "dataset_version": "TIV-DATASET-0001",
  "created_at": "2026-10-01T00:00:00Z",
  "created_by": "Tiv AI Pipeline Release Automation",
  "eligibility_policy_version": "v1.0",
  "quality_policy_version": "v1.0",
  "counts": {
    "total_records": 12500,
    "text_sentences": 6000,
    "translation_pairs": 4500,
    "speech_recordings": 2000
  },
  "speech_statistics": {
    "total_duration_seconds": 21600.0,
    "total_duration_hours": 6.0,
    "dialects": {
      "Central Tiv": 1400,
      "Eastern Tiv": 350,
      "Western Tiv": 200,
      "Other": 50
    },
    "canonical_format": "audio/wav; codec=pcm_s16le; rate=16000; channels=1"
  },
  "splits": {
    "train_ratio": 0.8,
    "dev_ratio": 0.1,
    "test_ratio": 0.1,
    "split_seed": 42
  },
  "checksum": "d5f6a7...sha256"
}
```

---

## 4. Future Machine Learning Interfaces

**IMPORTANT DIRECTIVE**: No machine learning models (ASR, TTS, MT, LLM) are trained during Milestone 0. However, the data platform's schemas and export contracts are explicitly engineered so that future ML engineers have turnkey access to structured datasets without requiring schema conversions or manual audio curation.

### 4.1 Interface: Automatic Speech Recognition (ASR)
- **Target Models**: Whisper (OpenAI), wav2vec 2.0 (Meta), Conformer (NeMo).
- **Target Artifact Format**:
  - Uncompressed 16 kHz 16-bit linear PCM WAV (`pcm_s16le`), mono channel.
  - Paired with normalized UTF-8 NFC Tiv transcript.
- **Manifest Record Structure (`data_speech.jsonl`)**:
  ```json
  {
    "id": "sub_01h8q7j4",
    "audio_filepath": "audio/sub_01h8q7j4_16k_mono.wav",
    "duration": 4.25,
    "text": "M ngu lamen zwa Tiv sha gbashima.",
    "speaker_id": "contrib_9876",
    "dialect": "Central Tiv",
    "split": "train"
  }
  ```

### 4.2 Interface: English ↔ Tiv Translation (Machine Translation)
- **Target Models**: NLLB-200 (Meta), mT5 (Google), Llama-3 fine-tuning.
- **Target Artifact Format**: Parallel sentence files (JSONL and standard TSV).
- **Manifest Record Structure (`data_translations.jsonl`)**:
  ```json
  {
    "id": "sub_02k9p8x1",
    "source_language": "en",
    "target_language": "tiv",
    "source_text": "Good morning, how is the family?",
    "target_text": "Nder ve, tsombor ngu nena?",
    "dialect": "Central Tiv",
    "split": "train"
  }
  ```

### 4.3 Interface: Tiv Conversational AI (Language Modeling)
- **Target Models**: Small instruction-tuned LLMs (Gemma, Llama, Mistral).
- **Target Artifact Format**: Multi-turn and instruction formatted JSONL.
- **Manifest Record Structure**:
  ```json
  {
    "id": "conv_03m7v1a2",
    "messages": [
      {"role": "user", "content": "Tiv kwagh u Benue State nena?"},
      {"role": "assistant", "content": "Benue State ka kpentar u i yer ér Food Basket of the Nation la..."}
    ],
    "dialect": "Central Tiv",
    "split": "train"
  }
  ```

### 4.4 Interface: Spoken Tiv Text-to-Speech (TTS)
- **Target Models**: VITS, Bark, Piper, FastSpeech 2.
- **Acoustic Preservations Note**:
  - Unlike ASR (which standardizes on 16 kHz mono), high-fidelity TTS requires wideband audio (22.05 kHz, 24 kHz, or 48 kHz) with pristine signal-to-noise ratios.
  - **Because Developer 3 preserves the original raw upload in `raw/audio/`**, future TTS pipelines can tap directly into uncompressed or high-bitrate raw inputs without being penalized by the 16 kHz downsampling applied to ASR artifacts.
