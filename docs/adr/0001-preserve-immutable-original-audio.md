# ADR 0001: Preserve Immutable Original Contributed Audio

## Status
Accepted

## Context
Contributors will submit audio recordings captured across various client devices and browsers (Opus/WebM, AAC/MP4, WAV, MP3). Downstream speech recognition (ASR) pipelines will require standardized 16 kHz 16-bit mono PCM audio. A common architectural temptation is to transcode uploads immediately upon receipt and overwrite or discard the original contributed audio file to save storage space.

However, audio processing requirements vary across machine learning disciplines:
- Automatic Speech Recognition (ASR) operates effectively on 16 kHz mono audio.
- High-fidelity neural Text-to-Speech (TTS) and voice conversion models require wideband audio (22.05 kHz, 24 kHz, or 48 kHz) to reproduce natural tone and acoustic realism.
- Audio codecs and preprocessing techniques continue to evolve. Destructive downsampling in place permanently discards acoustic information that can never be recovered.

## Decision
We will treat all contributed audio files as **strictly immutable**. 
1. The raw audio stream submitted by the contributor is written directly into the `raw/audio/` namespace without modification.
2. All normalized or transcoded formats (such as 16 kHz mono WAV for ASR) are treated as **derived artifacts** written to the `processed/audio/` namespace.
3. The raw audio object is never deleted or overwritten, except under legal consent revocation.

## Consequences
### Positive
- Preserves the acoustic integrity and frequency spectrum of all contributions for future research and wideband TTS modeling.
- Enables complete reproducibility: derived datasets can be re-generated from scratch if filtering or normalization algorithms change.
- Prevents silent audio degradation caused by multi-generational transcoding.

### Negative / Trade-offs
- Storage requirements are modestly higher because both raw files and derived artifacts coexist. Given modern storage costs (fractions of a cent per gigabyte on S3-compatible storage), this trade-off is overwhelmingly justified.
