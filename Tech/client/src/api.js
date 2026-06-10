const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(error.error || "Request failed");
  }

  return response.json();
}

export const getHealth = () => request("/health");
export const getEvents = () => request("/events");
export const createEvent = (payload) =>
  request("/events", { method: "POST", body: JSON.stringify(payload) });
export const getResources = () => request("/resources");
export const submitApplication = (payload) =>
  request("/applications", { method: "POST", body: JSON.stringify(payload) });
