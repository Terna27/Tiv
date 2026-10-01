import { useState } from "react";
import { submitText } from "../api/client";

const DIALECTS = ["Not sure", "Central Tiv", "Eastern Tiv", "Western Tiv", "Other"];

export default function ContributeText() {
  const [tivText, setTivText] = useState("");
  const [source, setSource] = useState("");
  const [dialect, setDialect] = useState(DIALECTS[0]);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!tivText.trim() || !consent) return;

    setStatus("loading");
    setErrorMsg("");
    try {
      // TODO once Day 4's contributor flow exists: pass the real
      // contributorId from context/session instead of "anonymous".
      await submitText({
        contributorId: "anonymous",
        tivText: tivText.trim(),
        source: source.trim(),
        dialect,
        consent,
      });
      setStatus("success");
      setTivText("");
      setSource("");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message || "Something went wrong. Please try again.");
    }
  }

  if (status === "success") {
    return (
      <section className="section">
        <div className="status-banner status-success">
          Thank you! Your Tiv sentence has been submitted for review.
        </div>
        <button className="btn btn-secondary" onClick={() => setStatus("idle")}>
          Submit another
        </button>
      </section>
    );
  }

  return (
    <section className="section">
      <h2>Contribute Tiv text</h2>
      <p style={{ color: "var(--color-muted)" }}>
        Example: <em>Tiv: "U sha doo?"</em>
      </p>

      {status === "error" && (
        <div className="status-banner status-error">{errorMsg}</div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="tivText">Tiv sentence</label>
          <textarea
            id="tivText"
            value={tivText}
            onChange={(e) => setTivText(e.target.value)}
            placeholder="Type or paste a Tiv sentence..."
            required
          />
        </div>

        <div className="field">
          <label htmlFor="dialect">Dialect (if known)</label>
          <select id="dialect" value={dialect} onChange={(e) => setDialect(e.target.value)}>
            {DIALECTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="source">Source / context (optional)</label>
          <input
            id="source"
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="e.g. everyday conversation, proverb, news"
          />
          <div className="hint">Helps reviewers understand where this text comes from.</div>
        </div>

        <div className="field checkbox-row">
          <input
            id="consent"
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            required
          />
          <label htmlFor="consent" style={{ fontWeight: 400 }}>
            I confirm I wrote or am authorized to share this text, and I consent
            to it being used to build the Tiv AI dataset.
          </label>
        </div>

        <button type="submit" className="btn btn-primary" disabled={status === "loading" || !tivText.trim() || !consent}>
          {status === "loading" ? "Submitting..." : "Submit"}
        </button>
      </form>
    </section>
  );
}
