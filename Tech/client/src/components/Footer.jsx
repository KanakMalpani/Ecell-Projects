import { company, navLinks, socialLinks } from "../data/site";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-gnn-navy py-10 text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 md:grid-cols-3 md:px-6">
        <div>
          <h3 className="text-lg font-bold">{company.name}</h3>
          <p className="mt-2 text-sm text-white/70">{company.address}</p>
          <p className="mt-1 text-sm text-white/70">{company.email}</p>
        </div>

        <div>
          <h4 className="font-bold text-gnn-gold">Quick Links</h4>
          <ul className="mt-3 space-y-2 text-sm">
            {navLinks.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="transition hover:text-gnn-gold">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-bold text-gnn-gold">Follow Us</h4>
          <ul className="mt-3 space-y-2 text-sm">
            {socialLinks.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="transition hover:text-gnn-gold"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="mt-8 text-center text-xs text-white/60">
        © {new Date().getFullYear()} {company.name}. All rights reserved.
      </p>
    </footer>
  );
}
