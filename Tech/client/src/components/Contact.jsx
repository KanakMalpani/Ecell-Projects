import { useState } from "react";
import { motion } from "framer-motion";
import { company } from "../data/site";

const initialForm = {
  name: "",
  email: "",
  phone: "",
  service: "Freight Forwarding",
  message: "",
};

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
  const [submitting, setSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    setStatus("");

    const scriptUrl = import.meta.env.VITE_GOOGLE_SCRIPT_URL;

    try {
      if (scriptUrl) {
        await fetch(scriptUrl, {
          method: "POST",
          mode: "no-cors",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...form,
            submittedAt: new Date().toISOString(),
          }),
        });
        setStatus("Thank you. Your inquiry was submitted successfully.");
      } else {
        setStatus(
          "Form validated successfully. Add VITE_GOOGLE_SCRIPT_URL to enable Google Sheets automation."
        );
      }
      setForm(initialForm);
    } catch {
      setStatus("Submission failed. Please try again or email us directly.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section id="contact" className="bg-gnn-slate py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:px-6">
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

        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg"
        >
          <div className="grid gap-4">
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
              disabled={submitting}
              className="rounded-full bg-gnn-red px-6 py-3 text-sm font-bold text-white transition hover:bg-red-700 disabled:opacity-60"
            >
              {submitting ? "Submitting..." : "Send Inquiry"}
            </button>

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
