/**
 * =============================================================================
 * Vite Configuration — Build Tool & Dev Server (vite.config.js)
 * =============================================================================
 *
 * PURPOSE:
 *   Configures how the project is served in development and bundled for production.
 *   Vite is the modern replacement for webpack/Create React App in this project.
 *
 * TECH STACK:
 *   - vite                  — core bundler + dev server (port 5173 by default)
 *   - @vitejs/plugin-react  — JSX transform + React Fast Refresh (HMR)
 *   - @tailwindcss/vite     — Tailwind CSS v4 integration (no PostCSS config needed)
 *
 * HOW VITE WORKS (INTERVIEW):
 *   DEV:  Serves source files as native ES modules — only transforms files on request.
 *         Result: near-instant cold start vs webpack's full-bundle approach.
 *   PROD: Rolls up everything into optimised static files in dist/ for Vercel deploy.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - defineConfig() gives TypeScript-style autocomplete in editors
 *   - react() plugin enables JSX in .jsx files without Babel config
 *   - tailwindcss() plugin scans JSX for class names and generates only used CSS
 *   - No custom build config needed — Vite conventions handle 90% of cases
 *   - Vercel auto-detects Vite: build command = npm run build, output = dist/
 *
 * DEPLOYMENT (VERCEL):
 *   npm run build  →  produces dist/index.html + dist/assets/*.js + dist/assets/*.css
 *   Vercel serves dist/ as a static site with SPA fallback to index.html
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    react(),       // JSX + Fast Refresh: edit a component, see changes without full reload
    tailwindcss(), // Processes @import "tailwindcss" in index.css and utility classes in JSX
  ],
});
