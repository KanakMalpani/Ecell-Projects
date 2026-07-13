/**
 * =============================================================================
 * About Component — Company Overview & Mission Section (About.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Builds trust by explaining who GNN Logistics is, what they do,
 *   and their mission. Alternating light background (bg-gnn-slate) for visual rhythm.
 *
 * LAYOUT (two-column responsive grid):
 *   Left:  "Company Overview" heading + mission text + 3 bullet points
 *   Right: "Our Mission" card with Founded year + Shipments/Year stats
 *
 * TECH STACK:
 *   - Framer Motion whileInView — scroll-triggered animations (not on page load)
 *   - company.mission from site.js — centralised content
 *   - Tailwind md:grid-cols-2 — single column mobile, two columns desktop
 *
 * ANIMATION PATTERN — "Scroll Reveal":
 *   Left panel slides from left (x: -20 → 0)
 *   Right panel slides from right (x: 20 → 0)
 *   viewport={{ once: true }} — animates only the first time user scrolls to it
 *
 * PI INTERVIEW TALKING POINTS:
 *   - whileInView vs animate: whileInView triggers on scroll, animate on mount
 *   - id="about" matches navLinks href="#about" for smooth-scroll navigation
 *   - Bullet points are hardcoded (could move to site.js for full data-driven approach)
 *   - Mission card uses shadow-lg + rounded-3xl for elevated card UI pattern
 *   - Stats in card (Founded 2016, 2.4M+ shipments) reinforce credibility
 */
import { motion } from "framer-motion";
import { company } from "../data/site";

export default function About() {
  return (
    <section id="about" className="bg-gnn-slate py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:items-center md:px-6">

        {/* LEFT COLUMN — company overview text and feature bullets */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-extrabold text-gnn-navy md:text-4xl">Company Overview</h2>
          <p className="mt-4 text-base leading-relaxed text-slate-700">{company.mission}</p>

          {/* Key differentiators — unordered list styled as bullet points */}
          <ul className="mt-6 space-y-3 text-sm font-semibold text-gnn-navy">
            <li>End-to-end shipment tracking and SLA reporting</li>
            <li>Dedicated account managers for enterprise clients</li>
            <li>Safety-first operations with audited warehouse facilities</li>
          </ul>
        </motion.div>

        {/* RIGHT COLUMN — mission statement card with stat tiles */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg"
        >
          <h3 className="text-xl font-bold text-gnn-red">Our Mission</h3>
          <p className="mt-3 text-slate-700">
            To make logistics predictable for growing businesses through technology-enabled
            operations, transparent pricing, and responsive customer care.
          </p>

          {/* STAT TILES — two-column mini-grid inside the mission card */}
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-gnn-slate p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Founded</p>
              <p className="text-lg font-bold">2016</p>
            </div>
            <div className="rounded-xl bg-gnn-slate p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Shipments / Year</p>
              <p className="text-lg font-bold">2.4M+</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
