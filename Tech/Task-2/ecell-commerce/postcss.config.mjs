/**
 * PostCSS configuration — processes CSS for Tailwind v4.
 *
 * The @tailwindcss/postcss plugin scans your source files and generates
 * utility classes (e.g. flex, p-4, text-zinc-900) at build time.
 */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
