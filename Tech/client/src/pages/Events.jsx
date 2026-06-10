import { useEffect, useState } from "react";
import { createEvent, getEvents } from "../api";

const initialForm = {
  title: "",
  description: "",
  date: "",
  domain: "tech",
  location: "NIT Trichy Campus",
};

export default function Events() {
  const [events, setEvents] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadEvents() {
    try {
      const data = await getEvents();
      setEvents(data);
      setStatus("");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await createEvent(form);
      setForm(initialForm);
      setStatus("Event created successfully.");
      await loadEvents();
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="page">
      <section className="hero">
        <h2>Club Events</h2>
        <p>Module 5-7 demo: React frontend talking to Express API and MongoDB.</p>
      </section>

      <section className="grid-2">
        <div className="card">
          <h3>Upcoming Events</h3>
          {loading && <p>Loading events...</p>}
          {!loading && events.length === 0 && <p>No events yet. Add one using the form.</p>}
          <div className="grid-2">
            {events.map((item) => (
              <article key={item._id} className="event-card">
                <span className="pill">{item.domain}</span>
                <h4>{item.title}</h4>
                <p>{item.description}</p>
                <small>
                  {item.date} - {item.location}
                </small>
              </article>
            ))}
          </div>
        </div>

        <div className="card">
          <h3>Add Event</h3>
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              Title
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
            </label>
            <label>
              Description
              <textarea
                rows="4"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
              />
            </label>
            <label>
              Date
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                required
              />
            </label>
            <label>
              Domain
              <select
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
              >
                <option value="tech">Tech</option>
                <option value="ai">AI &amp; Automation</option>
                <option value="design">Design</option>
                <option value="marketing">Marketing</option>
                <option value="all">All</option>
              </select>
            </label>
            <label>
              Location
              <input
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
              />
            </label>
            <button className="primary-btn" type="submit">
              Save Event
            </button>
          </form>
          {status && <p className={`status ${status.includes("success") ? "success" : "error"}`}>{status}</p>}
        </div>
      </section>
    </div>
  );
}
