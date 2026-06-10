import { NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import Events from "./pages/Events";
import Home from "./pages/Home";
import Join from "./pages/Join";
import Modules from "./pages/Modules";
import Resources from "./pages/Resources";

function App() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="brand">
          <img src="/ecell-logo.png" alt="E-Cell NIT Trichy logo" />
          <div>
            <h1>E-Cell NIT Trichy</h1>
            <p>Tech Induction MERN Project</p>
          </div>
        </div>
        <nav className="nav-links">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/modules">Modules</NavLink>
          <NavLink to="/events">Events</NavLink>
          <NavLink to="/resources">Resources</NavLink>
          <NavLink to="/join">Join</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/modules" element={<Modules />} />
        <Route path="/events" element={<Events />} />
        <Route path="/resources" element={<Resources />} />
        <Route path="/join" element={<Join />} />
      </Routes>

      <footer className="site-footer">
        <p>
          E-Cell Tech Induction | MERN Stack Project |{" "}
          <a href="https://github.com/KanakMalpani/Ecell-Projects" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
