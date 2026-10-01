import Nav from "./Nav";

export default function Layout({ children }) {
  return (
    <>
      <Nav />
      <main className="container">{children}</main>
      <footer>
        <div className="container">
          Tiv AI Platform — building open language technology for the Tiv language, with the Tiv community.
        </div>
      </footer>
    </>
  );
}
