/**
 * =============================================================================
 * Footer Component — Site Footer with Links & Social Media (Footer.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Bottom-of-page footer with company info, navigation links, social media,
 *   and auto-updating copyright year. Provides secondary navigation and trust signals.
 *
 * LAYOUT (three-column responsive grid):
 *   Column 1: Company name, physical address, email
 *   Column 2: Quick Links — same navLinks[] as Navbar (DRY via site.js)
 *   Column 3: Follow Us — socialLinks[] with target="_blank"
 *
 * TECH STACK:
 *   - Pure presentational component — no useState, no side effects
 *   - data/site.js imports — company, navLinks, socialLinks
 *   - new Date().getFullYear() — dynamic copyright year (no manual update needed)
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Footer reuses navLinks from site.js — single source of truth for navigation
 *   - target="_blank" + rel="noreferrer" on social links — opens new tab safely
 *     (noreferrer prevents referrer leakage and improves security)
 *   - Semantic <footer> element — screen readers identify page structure
 *   - No Framer Motion here — footer is below fold, animation adds little value
 *   - bg-gnn-navy matches Hero/Navbar — bookends the page with consistent branding
 *   - Dynamic year: new Date().getFullYear() runs client-side on each render
 */
import { company, navLinks, socialLinks } from "../data/site";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-gnn-navy py-10 text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 md:grid-cols-3 md:px-6">

        {/* COLUMN 1 — company identity and contact details */}
        <div>
          <h3 className="text-lg font-bold">{company.name}</h3>
          <p className="mt-2 text-sm text-white/70">{company.address}</p>
          <p className="mt-1 text-sm text-white/70">{company.email}</p>
        </div>

        {/* COLUMN 2 — page navigation (same links as Navbar, sourced from site.js) */}
        <div>
          <h4 className="font-bold text-gnn-gold">Quick Links</h4>
          <ul className="mt-3 space-y-2 text-sm">
            {navLinks.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="transition hover:text-gnn-gold">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* COLUMN 3 — social media links (open in new browser tab) */}
        <div>
          <h4 className="font-bold text-gnn-gold">Follow Us</h4>
          <ul className="mt-3 space-y-2 text-sm">
            {socialLinks.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="transition hover:text-gnn-gold"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* COPYRIGHT LINE — year generated dynamically at render time */}
      <p className="mt-8 text-center text-xs text-white/60">
        © {new Date().getFullYear()} {company.name}. All rights reserved.
      </p>
    </footer>
  );
}
