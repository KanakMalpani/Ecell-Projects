/**
 * React entry point — the first JavaScript file that runs.
 *
 * Flow:
 *   1. Find the <div id="root"> in index.html
 *   2. Create a React root on that element
 *   3. Render the <App /> component inside it
 *
 * StrictMode runs components twice in development to help catch bugs.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";   // global Tailwind styles + brand colours
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
