# Tiv AI — Frontend (Developer 2)

Data-collection website for the Tiv AI platform. Built with React + Vite.
This is Developer 2's part of the 3-developer, 1-week MVP sprint described
in the Tiv AI Data Collection Website roadmap.

## Run it

```bash
npm install
npm run dev
```

Visit http://localhost:5173

## What's here (Day 1)

- Routing shell: Home, About, Contribute (hub), Review
- Nav + responsive layout + shared design system in `src/styles/global.css`
- `src/api/client.js` — every API call the frontend needs, in **mock mode**
  by default so you're never blocked waiting on the backend
- `src/pages/ContributeText.jsx` — a **complete, working example** of a
  contribution form: use this as the template for Translation and Voice

## Your day-by-day (from the roadmap)

- **Day 1 (done):** foundation, nav, homepage, CTA, layout, design system
- **Day 2:** build `ContributeTranslation.jsx` following `ContributeText.jsx`'s
  pattern — fields: sourceText, targetText, sourceLanguage, targetLanguage,
  dialect, consent
- **Day 3:** build `ContributeVoice.jsx` — MediaRecorder for in-browser
  recording, plus a file-upload fallback; submit via `submitAudio()`
- **Day 4:** consent screen (gate before any contribution page), contributor
  dashboard / "My Contributions" history
- **Day 5:** `Review.jsx` — list submissions (`listSubmissions()`), a detail
  view, and Accept / Reject / Needs Correction buttons (`reviewSubmission()`)
- **Day 6:** test on real mobile + desktop, verify loading/error/success
  states everywhere, no new features
- **Day 7:** full walkthrough exactly as it'll be demoed; fix only what's broken

## Going live against the real backend

Every function in `src/api/client.js` is in mock mode (`USE_MOCKS = true`,
plus a per-endpoint toggle in `MOCK_ENDPOINTS`). As Developer 1 finishes each
endpoint:

1. Confirm the endpoint matches the agreed contract (see below).
2. Flip that endpoint's entry in `MOCK_ENDPOINTS` to `false`.
3. Set `VITE_API_BASE_URL` in a `.env` file if the backend isn't at
   `http://localhost:8000/api/v1`.

No page code needs to change — pages only ever call the functions in
`client.js`, never `fetch` directly.

## The API contract (agreed with Developer 1 & 3)

```
GET  /api/v1/health
POST /api/v1/contributors
GET  /api/v1/contributors/{id}
POST /api/v1/submissions/text
POST /api/v1/submissions/translations
POST /api/v1/submissions/audio
GET  /api/v1/submissions/{id}
GET  /api/v1/submissions
POST /api/v1/submissions/{id}/review
GET  /docs
```

If any of these shapes change, update `src/api/client.js` first — it's the
single place the rest of the app depends on.
