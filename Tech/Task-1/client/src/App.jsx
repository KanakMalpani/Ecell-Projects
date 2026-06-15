/**
 * Main page layout — stacks all sections vertically.
 *
 * Each section is its own component file in ./components/.
 * Content (text, services, testimonials) lives in ./data/site.js
 * so you can change copy without touching component logic.
 *
 * Page order (top to bottom):
 *   Navbar → Hero → About → Services → Testimonials → Contact → Footer
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
      {/* Sticky navigation bar — always visible at the top */}
      <Navbar />

      <main>
        {/* Hero: big headline + CTA buttons + stats */}
        <Hero />
        {/* About: company mission and overview */}
        <About />
        {/* Services: 4 service cards in a grid */}
        <Services />
        {/* Testimonials: 3 client quote cards */}
        <Testimonials />
        {/* Contact: inquiry form with validation */}
        <Contact />
      </main>

      {/* Footer: links, social media, copyright */}
      <Footer />
    </>
  );
}
