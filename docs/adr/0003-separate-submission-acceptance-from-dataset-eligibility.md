# ADR 0003: Separate Submission Acceptance from Dataset Eligibility

## Status
Accepted

## Context
In data collection systems, it is common to conflate human review approval (`ACCEPTED`) with readiness for machine learning dataset inclusion. However, this conflation creates severe vulnerabilities:
1. A reviewer might approve a voice submission based on accurate pronunciation, but the underlying audio stream might be truncated, clipped, or have missing provenance metadata.
2. A contributor might withdraw consent subsequent to reviewer approval. If dataset membership is synonymous with reviewer acceptance, revoked records could silently leak into training sets.
3. Automated quality validation criteria (e.g. minimum SNR, absence of digital clipping) must be enforceable without forcing human linguists to act as acoustic engineers.

## Decision
We decouple **Submission Review Status** (`SUBMITTED`, `UNDER_REVIEW`, `ACCEPTED`, `REJECTED`, `NEEDS_CORRECTION`) from **Dataset Eligibility** (`PENDING_REVIEW`, `ELIGIBLE`, `INELIGIBLE`, `EXCLUDED_BY_WITHDRAWAL`):
- Reviewer acceptance is a necessary condition, but **not a sufficient condition**, for dataset eligibility.
- A submission becomes `ELIGIBLE` only when:
  1. `review_status == ACCEPTED`
  2. `consent_status == TRUE` and not revoked
  3. Provenance and metadata are complete
  4. Raw storage artifact exists and passes checksum validation
  5. Automated quality checks evaluate to `PASS` or non-blocking `WARNING`

## Consequences
### Positive
- Strict quality and legal compliance: ML training datasets are guaranteed to contain only fully validated, consented, and verified audio.
- Clear separation of responsibilities: Reviewers focus purely on language and culture, while the automated engine enforces technical and legal constraints.
- Contributor consent revocations take immediate effect by flipping eligibility without mutating the historical review audit log.

### Negative / Trade-offs
- Requires maintaining two distinct status fields in the database schema (`review_status` and `dataset_eligibility`).
- Slightly more complex querying when constructing dataset manifests.
