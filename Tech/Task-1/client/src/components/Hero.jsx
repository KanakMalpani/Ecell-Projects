/**
 * =============================================================================
 * Hero Component — Above-the-Fold Landing Section (Hero.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   First section visitors see. Communicates value proposition, drives action
 *   via CTA buttons, and establishes brand credibility with stats.
 *
 * LAYOUT (responsive two-column grid):
 *   Left:  badge + headline + tagline + two CTA buttons
 *   Right: warehouse hero image + 3 stat cards (fleet, cities, on-time rate)
 *
 * TECH STACK:
 *   - Framer Motion motion.div — entrance animations on page load
 *   - Tailwind md:grid-cols-2  — stacks on mobile, side-by-side on desktop
 *   - company.tagline from site.js — dynamic content, static layout
 *
 * ANIMATION STRATEGY:
 *   Left column:  fade-up (opacity 0→1, y 24→0) — draws eye to headline first
 *   Right column: scale-in (opacity 0→1, scale 0.96→1) with 0.15s delay — staggered reveal
 *
 * PI INTERVIEW TALKING POINTS:
 *   - id="home" is the scroll target for navbar "Home" link
 *   - CTA buttons use anchor hrefs (#contact, #services) — no onClick handlers needed
 *   - Primary CTA (red) vs secondary CTA (outline) — visual hierarchy guides user action
 *   - Unsplash image with loading="eager" — prioritises LCP (Largest Contentful Paint)
 *   - width/height attributes prevent layout shift (CLS) while image loads
 *   - Stats (120+ fleet, 35 cities, 99% on-time) are hardcoded trust signals
 */
import { motion } from "framer-motion";
import { company } from "../data/site";

export default function Hero() {
  return (
    <section id="home" className="bg-gnn-navy text-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 md:grid-cols-2 md:items-center md:px-6 md:py-24">

        {/* LEFT COLUMN — headline, tagline, and call-to-action buttons */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Trust badge — gold pill above headline */}
          <p className="mb-3 inline-block rounded-full bg-gnn-gold px-3 py-1 text-xs font-bold uppercase tracking-wide text-gnn-navy">
            Trusted logistics partner
          </p>

          {/* Primary headline — largest text on the page */}
          <h1 className="text-4xl font-extrabold leading-tight md:text-5xl">
            Delivering reliability across every mile.
          </h1>

          {/* Dynamic tagline pulled from site.js company object */}
          <p className="mt-4 max-w-xl text-base text-white/80 md:text-lg">{company.tagline}</p>

          {/* CTA BUTTON GROUP — primary (filled) + secondary (outline) */}
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#contact"
              className="rounded-full bg-gnn-red px-6 py-3 text-sm font-bold transition hover:-translate-y-0.5 hover:bg-red-700"
            >
              Request a Quote
            </a>
            <a
              href="#services"
              className="rounded-full border border-white/30 px-6 py-3 text-sm font-bold transition hover:border-gnn-gold hover:text-gnn-gold"
            >
              Explore Services
            </a>
          </div>
        </motion.div>

        {/* RIGHT COLUMN — hero image with stat cards below */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6"
        >
          {/* Hero image — external Unsplash CDN, optimised with query params */}
          <img
            src="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=900&q=80"
            alt="Logistics warehouse operations"
            className="h-64 w-full rounded-2xl object-cover md:h-80"
            loading="eager"
            width="900"
            height="600"
          />

          {/* STAT CARDS — three-column grid of key business metrics */}
          <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
            <div className="rounded-xl bg-white/10 p-3">
              <p className="text-2xl font-bold text-gnn-gold">120+</p>
              <p className="text-white/70">Fleet Vehicles</p>
            </div>
            <div className="rounded-xl bg-white/10 p-3">
              <p className="text-2xl font-bold text-gnn-gold">35</p>
              <p className="text-white/70">Hub Cities</p>
            </div>
            <div className="rounded-xl bg-white/10 p-3">
              <p className="text-2xl font-bold text-gnn-gold">99%</p>
              <p className="text-white/70">On-time Rate</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
