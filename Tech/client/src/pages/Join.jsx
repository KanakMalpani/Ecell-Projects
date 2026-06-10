import { useState } from "react";
import { submitApplication } from "../api";

export default function Join() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    domain: "tech",
    message: "",
  });
  const [status, setStatus] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await submitApplication(form);
      setForm({ name: "", email: "", domain: "tech", message: "" });
      setStatus("Application submitted successfully.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="page">
      <section className="hero">
        <h2>Join E-Cell</h2>
        <p>Submit your interest for Tech or AI &amp; Automation domains.</p>
      </section>

      <section className="card" style={{ maxWidth: "640px" }}>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Full Name
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </label>
          <label>
            Preferred Domain
            <select
              value={form.domain}
              onChange={(e) => setForm({ ...form, domain: e.target.value })}
            >
              <option value="tech">Tech</option>
              <option value="ai">AI &amp; Automation</option>
              <option value="design">Design</option>
              <option value="marketing">Marketing</option>
            </select>
          </label>
          <label>
            Why do you want to join?
            <textarea
              rows="5"
              value={form.message}
              onChange={(e) => setForm({ ...form, message: e.target.value })}
            />
          </label>
          <button className="primary-btn" type="submit">
            Submit Application
          </button>
        </form>
        {status && (
          <p className={`status ${status.includes("success") ? "success" : "error"}`}>{status}</p>
        )}
      </section>
    </div>
  );
}
