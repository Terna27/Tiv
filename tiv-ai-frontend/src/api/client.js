/**
 * Central API client for the Tiv AI data collection site.
 *
 * MOCK MODE: while Developer 1's backend endpoints aren't ready yet,
 * this file returns realistic fake responses instead of making real
 * network calls, so you (Developer 2) are never blocked.
 *
 * TO GO LIVE: once an endpoint is confirmed working on Developer 1's
 * side, delete its entry from MOCK_ENDPOINTS below (or set
 * USE_MOCKS = false to flip everything at once). Nothing else in your
 * pages needs to change — they already call these functions.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Flip to false once the whole contract is live on Developer 1's side.
const USE_MOCKS = true;

// Per-endpoint mock toggle, so you can go live incrementally as each
// endpoint becomes real (recommended, matches "Day 2 text/translation,
// Day 3 audio, Day 5 review" rollout in the roadmap).
const MOCK_ENDPOINTS = {
  health: true,
  createContributor: true,
  submitText: true,
  submitTranslation: true,
  submitAudio: true,
  listSubmissions: true,
  getSubmission: true,
  reviewSubmission: true,
};

function delay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fakeId(prefix = "sub") {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

async function request(path, { method = "GET", body, isFormData = false } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: isFormData ? undefined : { "Content-Type": "application/json" },
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${errText || res.statusText}`);
  }
  return res.json();
}

// ---- health ----
export async function checkHealth() {
  if (USE_MOCKS && MOCK_ENDPOINTS.health) {
    await delay(150);
    return { status: "ok", mock: true };
  }
  return request("/health");
}

// ---- contributors ----
export async function createContributor({ displayName, consentStatus, dialect, metadata }) {
  if (USE_MOCKS && MOCK_ENDPOINTS.createContributor) {
    await delay();
    return { id: fakeId("contrib"), displayName, consentStatus, dialect, metadata, createdAt: new Date().toISOString() };
  }
  return request("/contributors", { method: "POST", body: { displayName, consentStatus, dialect, metadata } });
}

// ---- text submissions ----
export async function submitText({ contributorId, tivText, source, dialect, consent }) {
  if (USE_MOCKS && MOCK_ENDPOINTS.submitText) {
    await delay();
    return { id: fakeId("text"), status: "SUBMITTED", tivText, source, dialect, consent, createdAt: new Date().toISOString() };
  }
  return request("/submissions/text", { method: "POST", body: { contributorId, tivText, source, dialect, consent } });
}

// ---- translation submissions ----
export async function submitTranslation({ contributorId, sourceText, targetText, sourceLanguage, targetLanguage, dialect, consent }) {
  if (USE_MOCKS && MOCK_ENDPOINTS.submitTranslation) {
    await delay();
    return { id: fakeId("trans"), status: "SUBMITTED", sourceText, targetText, sourceLanguage, targetLanguage, dialect, consent, createdAt: new Date().toISOString() };
  }
  return request("/submissions/translations", { method: "POST", body: { contributorId, sourceText, targetText, sourceLanguage, targetLanguage, dialect, consent } });
}

// ---- audio submissions ----
export async function submitAudio({ contributorId, audioBlob, transcript, dialect, consent }) {
  if (USE_MOCKS && MOCK_ENDPOINTS.submitAudio) {
    await delay(700);
    return { id: fakeId("audio"), status: "SUBMITTED", transcript, dialect, consent, durationSeconds: 4.2, createdAt: new Date().toISOString() };
  }
  const form = new FormData();
  form.append("contributor_id", contributorId);
  form.append("audio_file", audioBlob, "recording.webm");
  form.append("transcript", transcript);
  form.append("dialect", dialect || "");
  form.append("consent", consent);
  return request("/submissions/audio", { method: "POST", body: form, isFormData: true });
}

// ---- review workflow ----
export async function listSubmissions({ status } = {}) {
  if (USE_MOCKS && MOCK_ENDPOINTS.listSubmissions) {
    await delay();
    return {
      items: [
        { id: "text_ab12cd34", type: "text", dialect: "Central Tiv", status: "SUBMITTED", preview: "U sha doo?", createdAt: new Date().toISOString() },
        { id: "trans_ef56gh78", type: "translation", dialect: "Central Tiv", status: "SUBMITTED", preview: "How are you? → Aôndo u yô?", createdAt: new Date().toISOString() },
        { id: "audio_ij90kl12", type: "audio", dialect: "Central Tiv", status: "UNDER_REVIEW", preview: "[4.2s recording]", createdAt: new Date().toISOString() },
      ].filter((item) => !status || item.status === status),
    };
  }
  return request(`/submissions${status ? `?status=${status}` : ""}`);
}

export async function getSubmission(id) {
  if (USE_MOCKS && MOCK_ENDPOINTS.getSubmission) {
    await delay();
    return { id, type: "text", tivText: "U sha doo?", dialect: "Central Tiv", status: "SUBMITTED", contributor: "Anonymous", createdAt: new Date().toISOString() };
  }
  return request(`/submissions/${id}`);
}

export async function reviewSubmission(id, { decision, notes }) {
  if (USE_MOCKS && MOCK_ENDPOINTS.reviewSubmission) {
    await delay();
    return { id, decision, notes, reviewedAt: new Date().toISOString() };
  }
  return request(`/submissions/${id}/review`, { method: "POST", body: { decision, notes } });
}
