/**
 * =============================================================================
 * React Entry Point — Application Bootstrap (main.jsx)
 * =============================================================================
 *
 * PURPOSE:
 *   The first JavaScript file that executes. Bridges index.html's #root div
 *   with the React component tree starting at <App />.
 *
 * TECH STACK:
 *   - react / react-dom/client  — createRoot API (React 18+ concurrent rendering)
 *   - StrictMode                — development-only double-render safety net
 *   - ./index.css               — global Tailwind import + brand theme tokens
 *   - ./App.jsx                 — root component composing all page sections
 *
 * EXECUTION FLOW:
 *   index.html loads this file
 *     → imports global CSS (Tailwind + brand colours)
 *     → finds <div id="root"> in the DOM
 *     → createRoot() attaches React's renderer to that element
 *     → render(<StrictMode><App /></StrictMode>) paints the full page
 *
 * PI INTERVIEW TALKING POINTS:
 *   - createRoot() replaced legacy ReactDOM.render() in React 18
 *   - StrictMode intentionally double-invokes renders/effects in DEV only
 *     to expose side-effect bugs (not a performance issue in production)
 *   - CSS imported here applies globally — component-scoped styles use Tailwind classes
 *   - Single entry point pattern: all routes/sections flow from App.jsx
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";   // Global Tailwind styles + GNN brand colour tokens
import App from "./App.jsx";

// Mount React app onto the #root element defined in index.html
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
