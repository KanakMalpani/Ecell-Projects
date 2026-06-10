import { useEffect, useState } from "react";
import { getResources } from "../api";

const moduleNames = {
  1: "HTML",
  2: "CSS",
  3: "JavaScript",
  4: "React",
  5: "Node.js & Express",
  6: "MongoDB",
  7: "MERN Stack",
  8: "Git & GitHub",
};

export default function Resources() {
  const [resources, setResources] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getResources()
      .then(setResources)
      .catch((err) => setError(err.message));
  }, []);

  const grouped = resources.reduce((acc, item) => {
    acc[item.module] = acc[item.module] || [];
    acc[item.module].push(item);
    return acc;
  }, {});

  return (
    <div className="page">
      <section className="hero">
        <h2>Learning Resources</h2>
        <p>Curated links from the E-Cell Tech induction PDF, served via the MERN API.</p>
      </section>

      {error && <p className="status error">{error}</p>}

      {Object.keys(grouped)
        .sort((a, b) => Number(a) - Number(b))
        .map((module) => (
          <section key={module} className="card">
            <h3>
              Module {module}: {moduleNames[module]}
            </h3>
            <div className="grid-2">
              {grouped[module].map((resource) => (
                <article key={resource._id} className="resource-item">
                  <span className="pill">{resource.type}</span>
                  <h4>{resource.title}</h4>
                  <p>{resource.description}</p>
                  <a href={resource.url} target="_blank" rel="noreferrer">
                    Open resource
                  </a>
                </article>
              ))}
            </div>
          </section>
        ))}
    </div>
  );
}
