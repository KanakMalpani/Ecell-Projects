/**
 * Next.js Configuration — build-time settings for the E-Cell Commerce app.
 *
 * ROLE IN THE APP:
 *   next.config.ts is evaluated at build time. It controls how Next.js bundles
 *   the app, which external image hosts are allowed, and what extra files get
 *   included in serverless function traces.
 *
 * KEY SETTINGS:
 *   images.remotePatterns — whitelist Unsplash CDN for next/image optimization
 *   outputFileTracingIncludes — bundle SQLite dev.db into API/page serverless
 *     functions so Prisma can read the database on Vercel's read-only filesystem
 *
 * PI INTERVIEW TALKING POINTS:
 *   - next/image requires explicit remote host allowlisting for security
 *   - Vercel serverless can't write to project dir; dev.db must be traced in
 *   - Alternative prod approach: PostgreSQL on Neon/Supabase instead of SQLite
 */
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  outputFileTracingIncludes: {
    "/api/*": ["./dev.db"],
    "/*": ["./dev.db"],
  },
};

export default nextConfig;
