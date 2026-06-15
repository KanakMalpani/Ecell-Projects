/**
 * Central content file for the GNN Logistics landing page.
 *
 * Keeping all text/data here means:
 *   - Components stay focused on layout and behaviour
 *   - A content editor only needs to edit THIS file
 *   - No hard-coded strings scattered across 7 component files
 *
 * Imported by: Navbar, Hero, About, Services, Testimonials, Contact, Footer
 */

// Company identity and contact details
export const company = {
  name: "GNN Logistics Inc.",
  tagline: "Moving business forward with precision and care.",
  mission:
    "GNN Logistics Inc. connects manufacturers, retailers, and enterprises to dependable freight, warehousing, and last-mile delivery networks. We combine route intelligence, transparent tracking, and responsive support to keep supply chains resilient.",
  phone: "+91 98765 43210",
  email: "contact@gnnlogistics.com",
  address: "Warehouse District, Trichy - 620015, Tamil Nadu, India",
};

// Four services shown in the Services section grid
export const services = [
  {
    title: "Freight Forwarding",
    description: "Road, rail, and multimodal freight planning with live shipment visibility.",
    icon: "truck",       // mapped to emoji in Services.jsx
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

// Three client testimonials shown in the Testimonials section
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

// Social media links in the Footer
export const socialLinks = [
  { label: "LinkedIn", href: "https://linkedin.com" },
  { label: "Instagram", href: "https://instagram.com" },
  { label: "X", href: "https://x.com" },
];

// Navigation menu items — hrefs match section id attributes for smooth scrolling
export const navLinks = [
  { label: "Home", href: "#home" },
  { label: "About", href: "#about" },
  { label: "Services", href: "#services" },
  { label: "Testimonials", href: "#testimonials" },
  { label: "Contact", href: "#contact" },
];
