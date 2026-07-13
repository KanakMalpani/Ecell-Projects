/**
 * =============================================================================
 * Contact Component — Inquiry Form with Client-Side Validation (Contact.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   Lead capture form for potential clients. Most logic-heavy component in the
 *   project — demonstrates React state management and form handling patterns.
 *
 * SUBMISSION STRATEGY — mailto: (no backend):
 *   1. User fills name, email, phone, service, message
 *   2. validate() runs on submit — returns errors object
 *   3. If valid, builds mailto: URL with encoded subject + body
 *   4. window.location.href opens user's default email client
 *   5. Success message shown, form resets to initialForm
 *
 * REACT STATE (three useState hooks):
 *   form    — controlled input values (single source of truth for all fields)
 *   errors  — per-field validation messages displayed below inputs
 *   status  — success banner text after successful submission
 *
 * SECURITY / SPAM:
 *   _honeypot hidden field — bots auto-fill it; if non-empty, submit silently ignored
 *
 * TECH STACK:
 *   - Controlled components — value={form.name} + onChange={handleChange}
 *   - Regex validation — email format and optional phone format
 *   - encodeURIComponent — safely encodes special chars in mailto: URL
 *   - Framer Motion — fade-in animation on scroll into view
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Why mailto: instead of API? Static site on Vercel — no server to receive POST
 *   - Controlled vs uncontrolled inputs: React owns the value via state (predictable)
 *   - Functional setState: setForm((current) => ...) avoids stale closure bugs
 *   - Clearing errors on handleChange gives instant feedback as user corrects input
 *   - event.preventDefault() stops browser's default form POST navigation
 *   - Production upgrade path: Formspree, Netlify Forms, or custom Express API
 *   - tabIndex={-1} + aria-hidden on honeypot keeps it out of keyboard navigation
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { company } from "../data/site";

// Default empty form — reused to reset all fields after successful submit
const initialForm = {
  name: "",
  email: "",
  phone: "",
  service: "Freight Forwarding",
  message: "",
  _honeypot: "",  // Spam trap — must remain empty for legitimate submissions
};

/**
 * Validates all form fields and returns an errors object.
 * Empty object {} means the form passed validation.
 * Each key maps to a user-friendly error message for that field.
 */
function validate(form) {
  const errors = {};

  // Name — required, non-empty after trimming whitespace
  if (!form.name.trim()) errors.name = "Name is required.";

  // Email — required + must match basic email regex pattern
  if (!form.email.trim()) {
    errors.email = "Email is required.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = "Enter a valid email address.";
  }

  // Phone — optional, but if provided must match international phone pattern
  if (form.phone && !/^\+?[\d\s-]{8,15}$/.test(form.phone)) {
    errors.phone = "Enter a valid phone number.";
  }

  // Message — required, non-empty after trimming
  if (!form.message.trim()) errors.message = "Please describe your inquiry.";

  return errors;
}

export default function Contact() {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("");

  /** Controlled input handler — updates one field and clears its error on edit */
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  }

  /** Form submit — validate, reject bots, open mailto:, show success, reset */
  function handleSubmit(event) {
    event.preventDefault();

    // Silently reject bot submissions that filled the hidden honeypot field
    if (form._honeypot) return;

    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    // Build mailto: URL with pre-filled subject and body for the email client
    const subject = encodeURIComponent(`GNN Logistics Inquiry - ${form.service}`);
    const body = encodeURIComponent(
      [
        `Name: ${form.name}`,
        `Email: ${form.email}`,
        `Phone: ${form.phone || "Not provided"}`,
        `Service: ${form.service}`,
        "",
        form.message,
      ].join("\n")
    );

    window.location.href = `mailto:${company.email}?subject=${subject}&body=${body}`;
    setStatus("Your email app should open with the inquiry ready to send.");
    setForm(initialForm);
  }

  return (
    <section id="contact" className="bg-gnn-slate py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:px-6">

        {/* LEFT COLUMN — contact information and response-time promise */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-extrabold text-gnn-navy md:text-4xl">Contact Us</h2>
          <p className="mt-3 text-slate-600">
            Tell us about your shipment volume, lanes, or warehousing needs. Our team responds
            within one business day.
          </p>

          {/* Company contact details from site.js */}
          <div className="mt-6 space-y-2 text-sm font-semibold text-gnn-navy">
            <p>Phone: {company.phone}</p>
            <p>Email: {company.email}</p>
            <p>Address: {company.address}</p>
          </div>
        </motion.div>

        {/* RIGHT COLUMN — inquiry form with validation */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg"
        >
          <div className="grid gap-4">

            {/* HONEYPOT FIELD — invisible to humans, catches spam bots */}
            <input
              type="text"
              name="_honeypot"
              value={form._honeypot}
              onChange={handleChange}
              tabIndex={-1}
              autoComplete="off"
              aria-hidden="true"
              className="hidden"
            />

            {/* FULL NAME — required text input */}
            <label className="text-sm font-semibold">
              Full Name
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-gnn-red"
              />
              {errors.name && <span className="mt-1 block text-xs text-gnn-red">{errors.name}</span>}
            </label>

            {/* EMAIL — required, type="email" gives browser-level format hint */}
            <label className="text-sm font-semibold">
              Email
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-gnn-red"
              />
              {errors.email && <span className="mt-1 block text-xs text-gnn-red">{errors.email}</span>}
            </label>

            {/* PHONE — optional; validated only if user enters a value */}
            <label className="text-sm font-semibold">
              Phone (optional)
              <input
                name="phone"
                value={form.phone}
                onChange={handleChange}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-gnn-red"
              />
              {errors.phone && <span className="mt-1 block text-xs text-gnn-red">{errors.phone}</span>}
            </label>

            {/* SERVICE DROPDOWN — pre-selected to "Freight Forwarding" */}
            <label className="text-sm font-semibold">
              Service
              <select
                name="service"
                value={form.service}
                onChange={handleChange}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-gnn-red"
              >
                <option>Freight Forwarding</option>
                <option>Warehousing</option>
                <option>Last-Mile Delivery</option>
                <option>Customs & Compliance</option>
              </select>
            </label>

            {/* MESSAGE — required textarea for inquiry details */}
            <label className="text-sm font-semibold">
              Message
              <textarea
                name="message"
                rows="4"
                value={form.message}
                onChange={handleChange}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-gnn-red"
              />
              {errors.message && (
                <span className="mt-1 block text-xs text-gnn-red">{errors.message}</span>
              )}
            </label>

            {/* SUBMIT BUTTON — triggers handleSubmit via form onSubmit */}
            <button
              type="submit"
              className="rounded-full bg-gnn-red px-6 py-3 text-sm font-bold text-white transition hover:bg-red-700"
            >
              Send Inquiry
            </button>

            {/* SUCCESS BANNER — conditionally rendered after successful submit */}
            {status && (
              <p className="rounded-xl bg-gnn-slate px-3 py-2 text-sm font-semibold text-gnn-navy">
                {status}
              </p>
            )}
          </div>
        </motion.form>
      </div>
    </section>
  );
}
