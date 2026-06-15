/**
 * Testimonials — three client review cards on a dark navy background.
 *
 * Data comes from testimonials[] in data/site.js.
 * Each card shows a quote, customer name (gold), and job title.
 *
 * Layout: 1 column on mobile, 3 columns on desktop (md:grid-cols-3).
 * Staggered fade-in animation as you scroll down the page.
 */
import { motion } from "framer-motion";
import { testimonials } from "../data/site";

export default function Testimonials() {
  return (
    <section id="testimonials" className="bg-gnn-navy py-16 text-white md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <h2 className="text-3xl font-extrabold md:text-4xl">Client Testimonials</h2>
        <p className="mt-3 max-w-2xl text-white/75">
          Businesses across retail, manufacturing, and food distribution rely on GNN Logistics.
        </p>

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
              <p className="text-sm leading-relaxed text-white/90">"{item.quote}"</p>
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
