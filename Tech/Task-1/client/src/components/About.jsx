/**
 * About — company overview and mission section.
 *
 * Layout: two columns
 *   Left:  company description + 3 bullet points
 *   Right: mission card with "Founded" and "Shipments/Year" stats
 *
 * Animation: slides in from left/right when scrolled into view.
 *   whileInView  — triggers animation when element enters the viewport
 *   viewport={{ once: true }} — only animates once (not on every scroll)
 */
import { motion } from "framer-motion";
import { company } from "../data/site";

export default function About() {
  return (
    <section id="about" className="bg-gnn-slate py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:items-center md:px-6">
        {/* Left: company overview text */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-extrabold text-gnn-navy md:text-4xl">Company Overview</h2>
          <p className="mt-4 text-base leading-relaxed text-slate-700">{company.mission}</p>
          <ul className="mt-6 space-y-3 text-sm font-semibold text-gnn-navy">
            <li>End-to-end shipment tracking and SLA reporting</li>
            <li>Dedicated account managers for enterprise clients</li>
            <li>Safety-first operations with audited warehouse facilities</li>
          </ul>
        </motion.div>

        {/* Right: mission card with key stats */}
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
