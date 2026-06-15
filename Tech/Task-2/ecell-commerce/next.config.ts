/**
 * Next.js configuration — image domains and deployment settings.
 *
 * remotePatterns: allows loading product images from Unsplash CDN.
 * outputFileTracingIncludes: bundles dev.db with serverless functions on Vercel.
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
