# Tiv AI — Data Collection Platform

> **Ethical, High-Quality Data Collection, Audio Ingestion & Curation Platform for the Tiv Language**

---

## 1. Project Mission & Overview

**Tiv AI** is an engineering initiative dedicated to collecting, validating, and curating high-quality linguistic resources for the Tiv language—spoken by millions across Benue State, neighboring regions in Nigeria, and the worldwide diaspora.

The long-term objective of Tiv AI is to power speech recognition (ASR), translation, conversational AI, and speech synthesis (TTS) models. To ensure success, the immediate milestone focuses entirely on the **Tiv AI Data Collection Platform**: an ingestion, validation, and review system engineered to gather:
1. **Monolingual Tiv Text** (everyday conversations, proverbs, literature).
2. **English ↔ Tiv Translation Pairs** (bidirectional parallel corpora).
3. **Spoken Tiv Audio** (in-browser recordings and voice uploads with accurate transcripts and dialect metadata).

> [!IMPORTANT]
> **No AI models are trained during this phase.** The platform prioritizes community trust, strict informed consent, lossless audio preservation, automated quality control, and human linguistic review.

---

## 2. Engineering Team Roles & Architecture Boundaries

Development is organized across three parallel, non-conflicting engineering streams:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DEVELOPER 2: FRONTEND & UX                            │
│  - Contributor Portal (React 19, Vite, responsive UI)                       │
│  - In-browser Audio Capture (MediaRecorder API) & Contribution Forms        │
│  - Consent Gating & Reviewer Dashboard UI                                   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON / Multipart
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER 1: BACKEND, API & DATABASE                     │
│  - FastAPI Web Application (`/api/v1`) & Pydantic Ingestion Schemas         │
│  - PostgreSQL Database (SQLAlchemy 2.0 ORM, Alembic Migrations)             │
│  - Contributor Session State & Review Queue Endpoints                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Python Service Calls
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               DEVELOPER 3: DATA PIPELINE, AUDIO & DEVOPS                    │
│  - Storage Abstraction Layer (Local Filesystem ↔ S3 Object Storage)         │
│  - Audio Media Probing & Server-Side Header Verification                    │
│  - Automated Quality Validation Engine (Silence, Clipping, Text Integrity)  │
│  - Cryptographic Deduplication (SHA-256) & Immutable Raw Ingestion          │
│  - Dataset Eligibility Rules & Versioned Manifest Engine                    │
│  - Future ML Export Interfaces & Localhost / CI Environments                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Engineering Documentation & Specifications

All technical specifications, API contracts, standards, and decision records are maintained in the [`docs/`](file:///home/recoding/Tiv/docs/) directory:

### 3.1 Architecture Specifications
- [**System Architecture**](file:///home/recoding/Tiv/docs/architecture/system-architecture.md): Component topology, service boundaries, localhost vs. production parity, and ownership matrix.
- [**Data Flow Architecture**](file:///home/recoding/Tiv/docs/architecture/data-flow.md): Step-by-step lifecycle flows for text, translation, and audio with Mermaid sequence diagrams.
- [**Storage Architecture**](file:///home/recoding/Tiv/docs/architecture/storage-architecture.md): Storage abstraction interface, namespaces (`raw/`, `processed/`, `quarantine/`, `exports/`), key generation, and consent withdrawal protocols.
- [**Dataset Lifecycle & ML Interfaces**](file:///home/recoding/Tiv/docs/architecture/dataset-lifecycle-and-ml-interfaces.md): Dataset eligibility rules, versioning conventions (`TIV-DATASET-xxxx`), and future ML export contracts (ASR, MT, Chat, TTS).

### 3.2 Technical Contracts
- [**Developer Integration Contract**](file:///home/recoding/Tiv/docs/contracts/integration-contract.md): End-to-end trace from Frontend → Backend → Data Pipeline → Database → Reviewer UI → Dataset Eligibility.
- [**Audio Ingestion Contract**](file:///home/recoding/Tiv/docs/contracts/audio-contract.md): Multipart form fields, accepted browser formats, file size & duration limits, and HTTP error schemas.
- [**Metadata & Provenance Contract**](file:///home/recoding/Tiv/docs/contracts/metadata-contract.md): Contribution metadata, audio technical metadata, demographic fields, governance records, and PostgreSQL schema blueprint.
- [**Submission Lifecycle Contract**](file:///home/recoding/Tiv/docs/contracts/submission-contract.md): Tri-state separation of Review Status, Automated Quality Status, and Dataset Eligibility.

### 3.3 Standards & Policies
- [**Audio Technical Standard**](file:///home/recoding/Tiv/docs/standards/audio-standard.md): Ingestion format vs. Canonical ASR format (16 kHz mono WAV), TTS wideband considerations, and acoustic thresholds.
- [**Data Quality Standard**](file:///home/recoding/Tiv/docs/standards/data-quality.md): Automated validation rules for text, translation, and audio; `PASS`/`WARNING`/`FAIL` grading; and SHA-256 deduplication strategy.
- [**Privacy & Consent Standard**](file:///home/recoding/Tiv/docs/standards/privacy-consent.md): Ethical principles, consent versioning, data minimization, private presigned audio access, and right-to-erasure workflows.

### 3.4 Architecture Decision Records (ADRs)
- [**ADR 0001: Preserve Immutable Original Audio**](file:///home/recoding/Tiv/docs/adr/0001-preserve-immutable-original-audio.md)
- [**ADR 0002: Abstract Storage Provider Layer**](file:///home/recoding/Tiv/docs/adr/0002-abstract-storage-provider.md)
- [**ADR 0003: Separate Submission Acceptance from Dataset Eligibility**](file:///home/recoding/Tiv/docs/adr/0003-separate-submission-acceptance-from-dataset-eligibility.md)
- [**ADR 0004: Checksum-Based Exact Duplicate Detection for MVP**](file:///home/recoding/Tiv/docs/adr/0004-checksum-based-exact-duplicate-detection.md)
- [**ADR 0005: Defer AI Model Training Outside Data Collection MVP**](file:///home/recoding/Tiv/docs/adr/0005-defer-ai-training-outside-data-collection-mvp.md)

---

## 4. Local Development Quickstart

### Prerequisites
- Python 3.12+
- Node.js 20+ and npm 10+
- PostgreSQL (or local SQLite for lightweight testing)

### Backend Setup (FastAPI)
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (once backend requirements are committed)
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Run database migrations
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup (React + Vite)
```bash
# Developer 2 frontend workspace
unzip -q tiv-ai-frontend.zip -d frontend
cd frontend
npm install
npm run dev
# Running on http://localhost:5173
```