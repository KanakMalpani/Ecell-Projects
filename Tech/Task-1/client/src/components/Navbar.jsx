/**
 * =============================================================================
 * Navbar Component — Sticky Header & Responsive Navigation (Navbar.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Persistent top navigation bar with logo, section links, and CTA button.
 *   Adapts layout: horizontal menu on desktop, hamburger dropdown on mobile.
 *
 * TECH STACK:
 *   - useState           — toggles mobile menu open/closed
 *   - Framer Motion      — AnimatePresence + motion.nav for slide-down animation
 *   - Tailwind responsive — hidden md:flex / md:hidden breakpoint pattern
 *   - data/site.js       — company name + navLinks array
 *
 * RESPONSIVE BREAKPOINTS (Tailwind md: = 768px+):
 *   Mobile  (<768px):  Logo + "Menu" button → animated dropdown
 *   Desktop (≥768px):  Logo + horizontal links + "Get a Quote" button
 *
 * PI INTERVIEW TALKING POINTS:
 *   - sticky top-0 z-50 keeps navbar above all content while scrolling
 *   - backdrop-blur + bg-gnn-navy/95 creates frosted-glass effect over hero
 *   - Anchor links (#about) + scroll-behavior:smooth in index.css = no router needed
 *   - AnimatePresence wraps conditional render — animates EXIT as well as enter
 *   - aria-expanded + aria-label on hamburger button = accessibility (a11y)
 *   - onClick={() => setOpen(false)} closes menu after link click (UX best practice)
 *   - navLinks.map() — DRY: same links used in Footer without duplication
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { company, navLinks } from "../data/site";

export default function Navbar() {
  // Mobile menu state: false = closed, true = dropdown visible
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-gnn-navy/95 text-white backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">

        {/* LOGO AREA — circular "G" badge + company name; links to #home */}
        <a href="#home" className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-gnn-gold font-bold text-gnn-navy">
            G
          </div>
          <div>
            <p className="text-sm font-bold leading-tight">{company.name}</p>
            <p className="text-xs text-white/70">Freight & Supply Chain</p>
          </div>
        </a>

        {/* DESKTOP NAV — hidden on mobile, flex row on md+ screens */}
        <nav className="hidden items-center gap-6 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-semibold transition hover:text-gnn-gold"
            >
              {link.label}
            </a>
          ))}
          {/* Primary CTA — same red button style used across Hero and Contact */}
          <a
            href="#contact"
            className="rounded-full bg-gnn-red px-4 py-2 text-sm font-bold transition hover:-translate-y-0.5 hover:bg-red-700"
          >
            Get a Quote
          </a>
        </nav>

        {/* MOBILE HAMBURGER — visible only below md breakpoint */}
        <button
          type="button"
          className="rounded-md border border-white/20 px-3 py-2 text-sm font-semibold md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-label="Toggle navigation menu"
        >
          Menu
        </button>
      </div>

      {/* MOBILE DROPDOWN — conditionally rendered with enter/exit animation */}
      <AnimatePresence>
        {open && (
          <motion.nav
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-white/10 md:hidden"
          >
            <div className="flex flex-col gap-3 px-4 py-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="font-semibold"
                  onClick={() => setOpen(false)}
                >
                  {link.label}
                </a>
              ))}
              <a
                href="#contact"
                className="rounded-full bg-gnn-red px-4 py-2 text-center font-bold"
                onClick={() => setOpen(false)}
              >
                Get a Quote
              </a>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}
