/**
 * Contact — inquiry form with client-side validation.
 *
 * This is the most logic-heavy component in the project.
 *
 * How the form works (NO backend server):
 *   1. User fills in name, email, phone, service, message
 *   2. validate() checks all fields on submit
 *   3. If valid, builds a mailto: link with pre-filled subject + body
 *   4. Opens the user's default email app via window.location.href
 *   5. Shows a success message and resets the form
 *
 * React state:
 *   form    — current values of all form fields
 *   errors  — validation error messages per field
 *   status  — success message shown after submit
 *
 * Honeypot: hidden _honeypot field — bots fill it, humans don't.
 *           If it has a value, submit is silently ignored.
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { company } from "../data/site";

// Default empty form state — also used to reset after successful submit
const initialForm = {
  name: "",
  email: "",
  phone: "",
  service: "Freight Forwarding",
  message: "",
  _honeypot: "",  // spam trap — must stay empty
};

/**
 * Validate form fields and return an errors object.
 * An empty errors object {} means the form is valid.
 */
function validate(form) {
  const errors = {};
  if (!form.name.trim()) errors.name = "Name is required.";
  if (!form.email.trim()) {
    errors.email = "Email is required.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = "Enter a valid email address.";
  }
  if (form.phone && !/^\+?[\d\s-]{8,15}$/.test(form.phone)) {
    errors.phone = "Enter a valid phone number.";
  }
  if (!form.message.trim()) errors.message = "Please describe your inquiry.";
  return errors;
}

export default function Contact() {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("");

  /** Update a single field value as the user types */
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));  // clear error on edit
  }

  /** Validate and open the email app with a pre-filled message */
  function handleSubmit(event) {
    event.preventDefault();

    // Silently reject if a bot filled the honeypot field
    if (form._honeypot) return;

    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;  // stop if validation failed

    // Build mailto: URL — opens the user's default email client
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
    setForm(initialForm);  // reset form after submit
  }

  return (
    <section id="contact" className="bg-gnn-slate py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:px-6">
        {/* Left: contact info text */}
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
          <div className="mt-6 space-y-2 text-sm font-semibold text-gnn-navy">
            <p>Phone: {company.phone}</p>
            <p>Email: {company.email}</p>
            <p>Address: {company.address}</p>
          </div>
        </motion.div>

        {/* Right: the inquiry form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg"
        >
          <div className="grid gap-4">
            {/* Honeypot — hidden from real users, catches spam bots */}
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

            {/* Full Name — required */}
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

            {/* Email — required, must be valid format */}
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

            {/* Phone — optional */}
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

            {/* Service dropdown */}
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

            {/* Message — required */}
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

            <button
              type="submit"
              className="rounded-full bg-gnn-red px-6 py-3 text-sm font-bold text-white transition hover:bg-red-700"
            >
              Send Inquiry
            </button>

            {/* Success message shown after form submits */}
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
