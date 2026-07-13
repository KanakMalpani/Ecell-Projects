/**
 * =============================================================================
 * Central Data Layer — Content & Configuration (data/site.js)
 * =============================================================================
 *
 * PURPOSE:
 *   Single source of truth for ALL static content on the landing page.
 *   Separates "what to show" (data) from "how to show it" (components).
 *
 * ARCHITECTURE PATTERN — "Data-Driven UI":
 *   Components import named exports and map over arrays to render UI.
 *   A content editor can update copy here without touching JSX logic.
 *
 * CONSUMERS (which components import what):
 *   company      → Navbar, Hero, About, Contact, Footer
 *   services[]   → Services (mapped to cards)
 *   testimonials[] → Testimonials (mapped to quote blocks)
 *   navLinks[]   → Navbar, Footer (mapped to anchor links)
 *   socialLinks[] → Footer (mapped to external links)
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Why a separate data file? DRY principle — nav links appear in Navbar AND Footer
 *   - href values (#home, #about) must match section id="" attributes in components
 *   - icon field in services uses string keys mapped to emojis in Services.jsx iconMap
 *   - In production, this could be replaced by a CMS API or JSON fetched at runtime
 *   - Named exports (not default) allow tree-shaking — only imported data gets bundled
 */

/* =========================================================================
   COMPANY IDENTITY — brand name, tagline, mission, and contact details
   ========================================================================= */
export const company = {
  name: "GNN Logistics Inc.",
  tagline: "Moving business forward with precision and care.",
  mission:
    "GNN Logistics Inc. connects manufacturers, retailers, and enterprises to dependable freight, warehousing, and last-mile delivery networks. We combine route intelligence, transparent tracking, and responsive support to keep supply chains resilient.",
  phone: "+91 98765 43210",
  email: "contact@gnnlogistics.com",
  address: "Warehouse District, Trichy - 620015, Tamil Nadu, India",
};

/* =========================================================================
   SERVICES — four offerings displayed as cards in Services.jsx
   icon: string key looked up in Services.jsx iconMap → emoji
   ========================================================================= */
export const services = [
  {
    title: "Freight Forwarding",
    description: "Road, rail, and multimodal freight planning with live shipment visibility.",
    icon: "truck",
  },
  {
    title: "Warehousing",
    description: "Secure storage, inventory control, and pick-pack operations at scale.",
    icon: "warehouse",
  },
  {
    title: "Last-Mile Delivery",
    description: "Urban and regional distribution with SLA-backed delivery windows.",
    icon: "route",
  },
  {
    title: "Customs & Compliance",
    description: "Documentation, clearance support, and regulatory guidance for cross-border cargo.",
    icon: "shield",
  },
];

/* =========================================================================
   TESTIMONIALS — client quotes for social proof in Testimonials.jsx
   ========================================================================= */
export const testimonials = [
  {
    quote:
      "GNN reduced our transit delays by 28% in the first quarter. Their team is proactive and easy to work with.",
    name: "Priya Menon",
    role: "Operations Head, Nova Retail",
  },
  {
    quote:
      "From warehousing to dispatch, the process is transparent. We finally have one partner for the full chain.",
    name: "Arjun Desai",
    role: "Supply Chain Manager, ForgeTech",
  },
  {
    quote:
      "Their customer support and tracking dashboard gave us confidence during peak festival season.",
    name: "Lakshmi Iyer",
    role: "Founder, Bloom Foods",
  },
];

/* =========================================================================
   SOCIAL LINKS — external URLs rendered in Footer "Follow Us" column
   ========================================================================= */
export const socialLinks = [
  { label: "LinkedIn", href: "https://linkedin.com" },
  { label: "Instagram", href: "https://instagram.com" },
  { label: "X", href: "https://x.com" },
];

/* =========================================================================
   NAVIGATION LINKS — anchor hrefs for smooth-scroll section navigation
   Each href must match a corresponding id="" on a <section> in a component
   ========================================================================= */
export const navLinks = [
  { label: "Home", href: "#home" },
  { label: "About", href: "#about" },
  { label: "Services", href: "#services" },
  { label: "Testimonials", href: "#testimonials" },
  { label: "Contact", href: "#contact" },
];
