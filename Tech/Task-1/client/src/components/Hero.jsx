/**
 * Hero — the first section visitors see (above the fold).
 *
 * Layout: two columns on desktop, stacked on mobile
 *   Left:  headline, tagline, two CTA buttons
 *   Right: warehouse image + 3 stat cards (fleet, cities, on-time rate)
 *
 * Animation: left column fades up, right column scales in (Framer Motion).
 * Section id="home" is the target for the navbar "Home" link.
 */
import { motion } from "framer-motion";
import { company } from "../data/site";

export default function Hero() {
  return (
    <section id="home" className="bg-gnn-navy text-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 md:grid-cols-2 md:items-center md:px-6 md:py-24">
        {/* Left column — text content */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}   // start invisible, shifted down
          animate={{ opacity: 1, y: 0 }}   // fade in and move to position
          transition={{ duration: 0.6 }}
        >
          <p className="mb-3 inline-block rounded-full bg-gnn-gold px-3 py-1 text-xs font-bold uppercase tracking-wide text-gnn-navy">
            Trusted logistics partner
          </p>
          <h1 className="text-4xl font-extrabold leading-tight md:text-5xl">
            Delivering reliability across every mile.
          </h1>
          <p className="mt-4 max-w-xl text-base text-white/80 md:text-lg">{company.tagline}</p>

          {/* CTA buttons — primary (red) and secondary (outline) */}
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

        {/* Right column — image and stat cards */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6"
        >
          <img
            src="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=900&q=80"
            alt="Logistics warehouse operations"
            className="h-64 w-full rounded-2xl object-cover md:h-80"
            loading="eager"
            width="900"
            height="600"
          />
          {/* Three quick-stat cards below the image */}
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
