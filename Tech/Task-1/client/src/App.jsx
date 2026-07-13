/**
 * =============================================================================
 * Root Application Component — Page Layout Orchestrator (App.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Composes the entire single-page landing site by stacking section components
 *   in reading order. No routing library needed — navigation uses anchor links.
 *
 * ARCHITECTURE PATTERN:
 *   - "Component composition" — each section is an isolated, reusable file
 *   - "Separation of concerns" — content lives in data/site.js, layout in components/
 *   - "Single-page layout" — one <main> with vertically stacked <section> elements
 *
 * PAGE STRUCTURE (top → bottom):
 *   Navbar      — sticky header, mobile hamburger menu
 *   Hero        — above-the-fold headline + CTAs + stats
 *   About       — company overview + mission card
 *   Services    — 4-card service grid
 *   Testimonials — 3 client quote cards
 *   Contact     — validated inquiry form (mailto: submission)
 *   Footer      — links, social media, copyright
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Why no React Router? Single landing page — anchor links (#about) are simpler
 *   - Fragment <> avoids extra DOM wrapper — Navbar outside <main> for semantics
 *   - <main> wraps primary content; Navbar/Footer are siblings (accessibility best practice)
 *   - Each section has id="..." matching navLinks hrefs in site.js for smooth scroll
 *   - Adding a new section = import component + drop it in the JSX tree
 */
import About from "./components/About";
import Contact from "./components/Contact";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import Navbar from "./components/Navbar";
import Services from "./components/Services";
import Testimonials from "./components/Testimonials";

export default function App() {
  return (
    <>
      {/* NAVBAR — sticky header, always visible; uses position:sticky via Tailwind */}
      <Navbar />

      {/* MAIN CONTENT — semantic HTML5 element for primary page content */}
      <main>
        {/* HERO — first impression section; id="home" is navbar "Home" anchor target */}
        <Hero />

        {/* ABOUT — company mission and key stats; id="about" for nav link */}
        <About />

        {/* SERVICES — responsive card grid driven by services[] in site.js */}
        <Services />

        {/* TESTIMONIALS — social proof section on dark navy background */}
        <Testimonials />

        {/* CONTACT — form with client-side validation; id="contact" for CTA buttons */}
        <Contact />
      </main>

      {/* FOOTER — site-wide links and copyright; outside <main> per HTML semantics */}
      <Footer />
    </>
  );
}
