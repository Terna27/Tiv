import { NavLink } from "react-router-dom";

export default function Nav() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <NavLink to="/" className="nav-brand">Tiv AI</NavLink>
        <div className="nav-links">
          <NavLink to="/about" className={({ isActive }) => (isActive ? "active" : "")}>
            About
          </NavLink>
          <NavLink to="/contribute" className={({ isActive }) => (isActive ? "active" : "")}>
            Contribute
          </NavLink>
          <NavLink to="/review" className={({ isActive }) => (isActive ? "active" : "")}>
            Review
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
