/**
 * =============================================================================
 * Services Component — Service Offerings Card Grid (Services.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Showcases GNN's four core logistics services as interactive cards.
 *   Data-driven rendering — adding a service in site.js auto-creates a card.
 *
 * DATA FLOW:
 *   site.js services[] → map() → motion.article card per service
 *   service.icon string → iconMap lookup → emoji displayed on card
 *
 * RESPONSIVE GRID:
 *   Mobile:  1 column (default)
 *   Tablet+: 2 columns (sm:grid-cols-2)
 *
 * TECH STACK:
 *   - Array.map() with key={service.title} — React list rendering best practice
 *   - Framer Motion whileInView + whileHover — scroll reveal + interactive lift
 *   - Staggered delay: index * 0.08s — cards appear sequentially, not all at once
 *
 * PI INTERVIEW TALKING POINTS:
 *   - iconMap object maps semantic keys ("truck") to emojis — could swap for SVG icons
 *   - whileHover={{ y: -4 }} gives tactile feedback without JavaScript event handlers
 *   - hover:border-gnn-gold + hover:shadow-md — CSS-only hover states via Tailwind
 *   - key={service.title} must be unique; using index as key is an anti-pattern here
 *   - White background section alternates with bg-gnn-slate (About) and bg-gnn-navy (Testimonials)
 */
import { motion } from "framer-motion";
import { services } from "../data/site";

// Maps icon string keys from site.js to emoji characters for visual identity
const iconMap = {
  truck: "🚚",
  warehouse: "🏭",
  route: "📦",
  shield: "🛡️",
};

export default function Services() {
  return (
    <section id="services" className="py-16 md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">

        {/* SECTION HEADER — title and introductory paragraph */}
        <div className="max-w-2xl">
          <h2 className="text-3xl font-extrabold text-gnn-navy md:text-4xl">Services Showcase</h2>
          <p className="mt-3 text-slate-600">
            Flexible logistics solutions designed for manufacturers, e-commerce brands, and
            enterprise supply teams.
          </p>
        </div>

        {/* SERVICE CARD GRID — one card per item in services[] */}
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {services.map((service, index) => (
            <motion.article
              key={service.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.08 }}
              whileHover={{ y: -4 }}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-gnn-gold hover:shadow-md"
            >
              {/* Service icon — emoji from iconMap lookup */}
              <div className="mb-4 text-3xl">{iconMap[service.icon]}</div>
              <h3 className="text-xl font-bold text-gnn-navy">{service.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{service.description}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
