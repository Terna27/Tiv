# Audio Ingestion Technical Contract

## 1. Overview & Agreement Scope

This contract establishes the formal technical agreement between:
- **Developer 2 (Frontend)**: Emits audio streams captured in browsers or selected via local upload.
- **Developer 1 (FastAPI Backend)**: Ingests multipart form submissions and manages HTTP request lifecycle.
- **Developer 3 (Data Infrastructure)**: Validates media binary headers, extracts acoustic parameters, persists immutable artifacts, and performs automated quality control.

---

## 2. Ingestion Endpoint Specification

- **Endpoint**: `POST /api/v1/submissions/audio`
- **Content-Type**: `multipart/form-data`
- **Authentication / Session**: Bearer token or Contributor Session Header (optional in early Week-1 mock mode, mandatory in production).

### 2.1 Form Field Definitions

| Field Name | Type | Presence | Description & Constraints |
| :--- | :--- | :--- | :--- |
| `audio_file` | Binary File | **Required** | Raw audio file or browser recording blob. Size: 1 KB – 25 MB. |
| `contributor_id` | String | **Required** | UUID or system identifier of contributor (e.g. `contrib_01h8...`). |
| `transcript` | String | **Required** | The Tiv sentence or prompt spoken in the recording. Min 1, Max 1000 chars. |
| `dialect` | String | Optional | Dialect tag: `"Central Tiv"`, `"Eastern Tiv"`, `"Western Tiv"`, `"Other"`, or `"Not sure"`. |
| `consent` | Boolean / String | **Required** | Contributor consent confirmation. Must equal `true` or `"true"`. |
| `client_metadata`| String (JSON) | Optional | Client environment metadata (browser, platform, client-measured duration). |

> **IMPORTANT NAMING CONVENTION NOTE**:
> To resolve naming disparities between Developer 2's JSON payloads (which use camelCase like `contributorId`) and `FormData` submissions in `src/api/client.js` (which use snake_case like `contributor_id`), Developer 1's FastAPI schema will accept **both** `contributor_id` and `contributorId`, but `contributor_id` is the canonical standard.

---

## 3. Accepted Browser & Upload Formats

In-browser recording behaviors vary substantially across platforms:
- **Chrome / Firefox / Edge / Android**: Default to `audio/webm;codecs=opus` or `audio/ogg`.
- **Safari / iOS (WebKit)**: Defaults to `audio/mp4` or `audio/aac` (MediaRecorder in WebKit does not reliably support Opus/WebM in all iOS versions).
- **Desktop File Uploads**: Users may upload standard pre-recorded files in `.wav`, `.mp3`, or `.m4a`.

### Matrix of Accepted Ingestion Containers & Codecs:

| Container Format | Typical MIME Type | Supported Codecs | Typical Source |
| :--- | :--- | :--- | :--- |
| **WebM** | `audio/webm`, `video/webm` | Opus, Vorbis | Chrome / Firefox MediaRecorder |
| **Ogg** | `audio/ogg`, `application/ogg` | Opus, Vorbis | Linux / Firefox MediaRecorder |
| **MP4 / M4A** | `audio/mp4`, `audio/x-m4a`, `audio/aac` | AAC, ALAC | Safari / iOS MediaRecorder, Voice Memos |
| **WAV** | `audio/wav`, `audio/x-wav` | Linear PCM (16/24-bit) | Desktop microphone / studio recording |
| **MP3** | `audio/mpeg`, `audio/mp3` | MPEG Layer 3 | Contributed pre-existing voice clips |

---

## 4. Size & Duration Constraints

- **Minimum File Size**: `1,024 bytes` (1 KB). Prevents empty or 0-byte header-only files.
- **Maximum File Size**: `26,214,400 bytes` (25 MB). Sufficient for up to 10 minutes of uncompressed WAV or hours of compressed Opus; protects server against memory/disk exhaustion.
- **Minimum Duration**: `0.5 seconds`. Rejects accidental clicks, instantaneous taps, and empty recordings.
- **Maximum Duration**: `120.0 seconds` (2 minutes). Targets sentence- and short-passage-level speech suitable for ASR alignment and TTS modeling.

---

## 5. Verification Rules: Zero Trust on Headers & Extensions

**CRITICAL SECURITY & RELIABILITY RULE**:
1. **Never trust `Content-Type` headers**: Browsers frequently report incorrect, generic (`application/octet-stream`), or manipulated MIME types.
2. **Never trust file extensions**: In `client.js`, Developer 2 passes `recording.webm` as the default filename for all blobs, even if recorded on iOS as AAC/MP4.

### Server-Side Inspection Protocol (Developer 3):
Developer 3's media probe inspects the binary stream header (magic bytes) using server-side media inspection libraries (`soundfile`, `mutagen`, or `ffprobe` / `av`):
1. **Header Sniffing**: Match first bytes against known container signatures (e.g. `1A 45 DF A3` for EBML/WebM; `OggS` for Ogg; `ftyp` for MP4/AAC; `RIFF....WAVE` for WAV; `ID3` or `FF FB` for MP3).
2. **Header Decode**: Read the audio header to extract:
   - Actual codec
   - Sample rate (Hz)
   - Channel count (1=mono, 2=stereo)
   - Duration (seconds)
3. **Decodability Check**: Read the first audio frame to verify the container is not truncated or corrupted.

---

## 6. HTTP Status Codes & Error Contract

Developer 1's API must return standardized HTTP status codes and structured JSON error responses:

| HTTP Status | Trigger Condition | Error Code (`code`) | Actionable Message to Developer 2 |
| :--- | :--- | :--- | :--- |
| **400 Bad Request** | Missing required form field or `consent != true` | `MISSING_FIELD` / `CONSENT_REQUIRED` | "You must provide your consent before submitting." |
| **413 Payload Too Large** | Uploaded file exceeds 25 MB | `FILE_TOO_LARGE` | "Audio file exceeds 25 MB limit." |
| **415 Unsupported Media Type**| Unrecognized magic bytes or unsupported codec | `UNSUPPORTED_MEDIA` | "The uploaded audio format is not supported. Please use WebM, WAV, MP4, or MP3." |
| **422 Unprocessable Content**| File corrupt, duration < 0.5s or > 120s | `AUDIO_DURATION_OUT_OF_BOUNDS` / `CORRUPT_AUDIO` | "Recording must be between 0.5 and 120 seconds." |
| **500 Internal Error** | Storage provider failure or uncaught server error | `STORAGE_ERROR` | "Temporary storage error. Please try again shortly." |

### Standard Error Response Schema:
```json
{
  "error": {
    "code": "AUDIO_DURATION_OUT_OF_BOUNDS",
    "message": "Recording duration of 0.32s is below the minimum allowed duration of 0.5s.",
    "details": {
      "measured_duration": 0.32,
      "min_allowed_duration": 0.5,
      "max_allowed_duration": 120.0
    }
  }
}
```

---

## 7. Success Response Contract

Upon successful ingestion, validation, and storage write, the API returns `201 Created` with the registered submission:

```json
{
  "id": "sub_01h8q7j4m3p0",
  "status": "SUBMITTED",
  "type": "audio",
  "transcript": "M ngu lamen zwa Tiv sha gbashima.",
  "dialect": "Central Tiv",
  "duration_seconds": 4.25,
  "technical_metadata": {
    "container": "webm",
    "codec": "opus",
    "sample_rate": 48000,
    "channels": 1,
    "file_size_bytes": 68420,
    "checksum_sha256": "3a4b5c6d7e8f..."
  },
  "created_at": "2026-09-23T12:00:00Z"
}
```
