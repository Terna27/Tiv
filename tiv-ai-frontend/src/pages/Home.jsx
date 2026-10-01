import { Link } from "react-router-dom";

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>Help build AI technology for the Tiv language</h1>
        <p>
          Tiv is spoken by millions of people, but almost no AI or translation
          tools understand it. We're building a Tiv text, speech, and
          translation platform &mdash; and we need native Tiv speakers to
          contribute real language data to make it work.
        </p>
        <Link to="/contribute" className="btn btn-primary">Contribute to Tiv AI</Link>
      </section>

      <section className="section">
        <h2>What your contribution supports</h2>
        <div className="card">
          <strong>Speech recognition</strong> &mdash; teaching computers to understand spoken Tiv.
        </div>
        <div className="card">
          <strong>Translation</strong> &mdash; accurate English &harr; Tiv translation.
        </div>
        <div className="card">
          <strong>Conversation &amp; speech synthesis</strong> &mdash; a Tiv-speaking assistant that can talk back.
        </div>
      </section>

      <section className="section">
        <h2>How it works</h2>
        <div className="card">
          <p style={{ margin: 0 }}>
            1. Give consent &rarr; 2. Contribute a Tiv sentence, translation, or
            voice recording &rarr; 3. Our team reviews it &rarr; 4. It becomes part
            of an open, versioned Tiv dataset used to train the models.
          </p>
        </div>
      </section>
    </>
  );
}
