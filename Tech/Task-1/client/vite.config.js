/**
 * Vite build tool configuration.
 *
 * Plugins:
 *   react()       — enables JSX syntax and React Fast Refresh in dev
 *   tailwindcss() — processes Tailwind utility classes in CSS/JSX
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
