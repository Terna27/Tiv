import { Link } from "react-router-dom";

const OPTIONS = [
  {
    to: "/contribute/text",
    title: "Contribute Tiv text",
    desc: "Share a sentence or short passage written in Tiv.",
  },
  {
    to: "/contribute/translation",
    title: "Contribute a translation",
    desc: "Provide an English↔Tiv translation pair.",
  },
  {
    to: "/contribute/voice",
    title: "Contribute your voice",
    desc: "Record or upload yourself speaking Tiv.",
  },
];

export default function Contribute() {
  return (
    <section className="section">
      <h2>Choose how you'd like to contribute</h2>
      <p style={{ color: "var(--color-muted)" }}>
        Every contribution type asks for your consent first, and takes just
        a few minutes.
      </p>
      {OPTIONS.map((opt) => (
        <Link key={opt.to} to={opt.to} className="card" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <strong>{opt.title}</strong>
          <p style={{ margin: "6px 0 0", color: "var(--color-muted)" }}>{opt.desc}</p>
        </Link>
      ))}
    </section>
  );
}
