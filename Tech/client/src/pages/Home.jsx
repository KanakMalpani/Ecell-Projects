const roadmap = [
  { step: 1, title: "HTML", detail: "Semantic structure, forms, tables, and links." },
  { step: 2, title: "CSS", detail: "Flexbox, grid, and E-Cell brand styling." },
  { step: 3, title: "JavaScript", detail: "DOM manipulation, filters, and local storage." },
  { step: 4, title: "React", detail: "Component-based UI for this MERN application." },
  { step: 5, title: "Node & Express", detail: "REST API powering events and applications." },
  { step: 6, title: "MongoDB", detail: "Persistent storage for club data." },
  { step: 7, title: "MERN Stack", detail: "Full integration across frontend, backend, and DB." },
  { step: 8, title: "Git & GitHub", detail: "Version control and collaborative workflows." },
];

export default function Home() {
  return (
    <div className="page">
      <section className="hero">
        <div className="hero-grid">
          <div>
            <span className="hero-badge">E-Cell Tech Induction</span>
            <h2>Build. Launch. Lead.</h2>
            <p>
              This project completes the E-Cell web development roadmap from static HTML pages
              to a full MERN application using the official club theme colors.
            </p>
          </div>
          <div className="card">
            <h3>What you will explore</h3>
            <ul>
              <li>Static modules in <code>modules/</code> for HTML, CSS, and JavaScript</li>
              <li>React frontend with routing and API integration</li>
              <li>Express + MongoDB backend for events and applications</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="card">
        <h3>8-Step Learning Roadmap</h3>
        <div className="grid-2">
          {roadmap.map((item) => (
            <article key={item.step} className="module-card">
              <strong>
                {item.step}. {item.title}
              </strong>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
