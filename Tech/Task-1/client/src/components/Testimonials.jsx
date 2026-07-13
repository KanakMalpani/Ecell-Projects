/**
 * =============================================================================
 * Testimonials Component — Client Social Proof Section (Testimonials.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Displays customer quotes to build credibility and trust.
 *   Dark navy background (bg-gnn-navy) creates visual contrast with adjacent sections.
 *
 * DATA FLOW:
 *   site.js testimonials[] → map() → motion.blockquote per testimonial
 *
 * LAYOUT:
 *   Mobile:  1 column (stacked quote cards)
 *   Desktop: 3 columns (md:grid-cols-3) — one card per testimonial
 *
 * TECH STACK:
 *   - Semantic <blockquote> + <footer> — proper HTML for quoted content
 *   - Framer Motion staggered whileInView — cards fade in sequentially on scroll
 *   - testimonials from site.js — name, role, quote all externalised
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Social proof is a key conversion element on landing pages
 *   - blockquote is semantically correct HTML (better than div for quotes)
 *   - footer inside blockquote holds attribution (name + role) per HTML5 spec
 *   - bg-white/5 creates subtle glass effect on dark background (5% white opacity)
 *   - Stagger delay index * 0.1s — slightly slower than Services for dramatic effect
 *   - Could extend with star ratings, company logos, or a carousel for more testimonials
 */
import { motion } from "framer-motion";
import { testimonials } from "../data/site";

export default function Testimonials() {
  return (
    <section id="testimonials" className="bg-gnn-navy py-16 text-white md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">

        {/* SECTION HEADER */}
        <h2 className="text-3xl font-extrabold md:text-4xl">Client Testimonials</h2>
        <p className="mt-3 max-w-2xl text-white/75">
          Businesses across retail, manufacturing, and food distribution rely on GNN Logistics.
        </p>

        {/* TESTIMONIAL CARD GRID — maps over testimonials array from site.js */}
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {testimonials.map((item, index) => (
            <motion.blockquote
              key={item.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: index * 0.1 }}
              className="rounded-2xl border border-white/10 bg-white/5 p-6"
            >
              {/* Client quote — wrapped in typographic quotation marks */}
              <p className="text-sm leading-relaxed text-white/90">"{item.quote}"</p>

              {/* Attribution — client name (gold) and job title */}
              <footer className="mt-4">
                <p className="font-bold text-gnn-gold">{item.name}</p>
                <p className="text-xs text-white/70">{item.role}</p>
              </footer>
            </motion.blockquote>
          ))}
        </div>
      </div>
    </section>
  );
}
