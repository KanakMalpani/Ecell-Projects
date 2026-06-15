/**
 * Services — grid of 4 service cards.
 *
 * Data comes from services[] in data/site.js.
 * Each card shows an emoji icon, title, and description.
 *
 * Responsive grid:
 *   mobile  → 1 column
 *   tablet+ → 2 columns (sm:grid-cols-2)
 *
 * Hover effect: card lifts up slightly (whileHover={{ y: -4 }}).
 * Staggered animation: each card delays 0.08s so they appear one after another.
 */
import { motion } from "framer-motion";
import { services } from "../data/site";

// Maps the icon string from site.js to an emoji displayed on each card
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
        <div className="max-w-2xl">
          <h2 className="text-3xl font-extrabold text-gnn-navy md:text-4xl">Services Showcase</h2>
          <p className="mt-3 text-slate-600">
            Flexible logistics solutions designed for manufacturers, e-commerce brands, and
            enterprise supply teams.
          </p>
        </div>

        {/* Map over services array — one card per service */}
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {services.map((service, index) => (
            <motion.article
              key={service.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.08 }}  // stagger effect
              whileHover={{ y: -4 }}  // lift on hover
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-gnn-gold hover:shadow-md"
            >
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
