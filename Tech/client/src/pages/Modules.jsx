const modules = [
  {
    title: "Module 1 - HTML",
    path: "/modules/01-html/index.html",
    summary: "Semantic structure, tables, forms, and navigation links.",
  },
  {
    title: "Module 2 - CSS",
    path: "/modules/02-css/index.html",
    summary: "E-Cell theme colors, Flexbox team cards, and CSS Grid calendar.",
  },
  {
    title: "Module 3 - JavaScript",
    path: "/modules/03-javascript/index.html",
    summary: "Event filters, RSVP counter, and local storage contact list.",
  },
];

export default function Modules() {
  return (
    <div className="page">
      <section className="hero">
        <h2>Static Learning Modules</h2>
        <p>Open the beginner HTML, CSS, and JavaScript demos built for induction.</p>
      </section>

      <section className="grid-3">
        {modules.map((module) => (
          <article key={module.title} className="module-card">
            <h3>{module.title}</h3>
            <p>{module.summary}</p>
            <a className="secondary-btn" href={module.path} target="_blank" rel="noreferrer">
              Open demo
            </a>
          </article>
        ))}
      </section>
    </div>
  );
}
