export default function About() {
  return (
    <section className="section">
      <h2>About this project</h2>
      <p>
        The Tiv AI project is building the first coordinated set of AI tools
        for the Tiv language: text understanding, English &harr; Tiv
        translation, speech recognition, a conversational assistant, and
        speech synthesis. None of this is possible without real Tiv language
        data contributed by Tiv speakers &mdash; that's what this site is for.
      </p>

      <h2>How to contribute</h2>
      <ol>
        <li>Read and accept the consent terms.</li>
        <li>
          Choose a contribution type: a Tiv sentence, an English&harr;Tiv
          translation pair, or a spoken Tiv recording.
        </li>
        <li>Submit it with any relevant details (dialect, context).</li>
        <li>
          Our review team checks each submission before it's added to the
          official dataset.
        </li>
      </ol>

      <h2>Your data, your rights</h2>
      <p>
        We only collect what's needed to build a high-quality dataset. You
        explicitly consent before anything is submitted, and you can see
        your own contribution history at any time.
      </p>
    </section>
  );
}
