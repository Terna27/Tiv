# ADR 0005: Defer AI Model Training Outside Data Collection MVP

## Status
Accepted

## Context
The long-term mission of the Tiv AI project is to build speech recognition (ASR), translation, conversational assistants, and speech synthesis (TTS) for the Tiv language. AI model training requires high-quality, cleanly curated, well-annotated, and legally consented linguistic data.

Embarking on model training prematurely—before the foundational data platform has collected, verified, and structured sufficient training data—creates severe operational risks:
1. Model performance will be compromised by noisy, misaligned, or corrupt input data.
2. Engineering focus will be diverted away from contributor UX, audio validation, storage security, and human review workflows.
3. Heavy ML dependencies (CUDA, PyTorch, Hugging Face Transformers, large GPU infrastructure) complicate local development for team members focused on frontend and backend APIs.

## Decision
We strictly enforce that **no model training (ASR, TTS, translation, or LLM) will take place during Milestone 0 and the Week-1 Data Collection MVP**.
- The engineering team's sole objective is building a production-grade data collection and curation platform.
- The platform will engineer clean, standardized export interfaces (`TIV-DATASET-xxxx` manifests, 16 kHz mono WAV derivatives, parallel TSVs) so that downstream ML training can begin seamlessly in subsequent milestones once sufficient verified data has been collected.

## Consequences
### Positive
- Maximizes engineering throughput on data quality, contributor experience, and infrastructure reliability.
- Keeps repository lightweight and fast to clone, test, and run on standard developer laptops without specialized GPUs.
- Ensures ethical compliance: data is verified, consented, and audited before any model learns from it.

### Negative / Trade-offs
- AI demonstrations are deferred until high-quality, verified data reaches statistical significance.
