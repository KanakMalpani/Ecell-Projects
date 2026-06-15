import { motion } from "framer-motion";
import { services } from "../data/site";

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
