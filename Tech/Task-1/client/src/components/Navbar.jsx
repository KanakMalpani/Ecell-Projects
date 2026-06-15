/**
 * Navbar — sticky top navigation bar.
 *
 * Desktop (md+): logo + horizontal menu links + "Get a Quote" button
 * Mobile:        hamburger "Menu" button that toggles a dropdown
 *
 * React concepts used:
 *   useState     — tracks whether the mobile menu is open
 *   AnimatePresence + motion.nav — smooth slide-down animation (Framer Motion)
 *
 * Navigation uses anchor links (#home, #about, etc.) for smooth scrolling.
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { company, navLinks } from "../data/site";

export default function Navbar() {
  // false = menu closed, true = menu open (mobile only)
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-gnn-navy/95 text-white backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">
        {/* Logo — links back to the top of the page */}
        <a href="#home" className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-gnn-gold font-bold text-gnn-navy">
            G
          </div>
          <div>
            <p className="text-sm font-bold leading-tight">{company.name}</p>
            <p className="text-xs text-white/70">Freight & Supply Chain</p>
          </div>
        </a>

        {/* Desktop navigation — hidden on mobile (hidden md:flex) */}
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
          <a
            href="#contact"
            className="rounded-full bg-gnn-red px-4 py-2 text-sm font-bold transition hover:-translate-y-0.5 hover:bg-red-700"
          >
            Get a Quote
          </a>
        </nav>

        {/* Mobile hamburger button — only visible on small screens (md:hidden) */}
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

      {/* Mobile dropdown menu — animated open/close with Framer Motion */}
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
                  onClick={() => setOpen(false)}  // close menu after clicking a link
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
