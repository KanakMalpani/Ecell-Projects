/**
 * Prisma Database Client — singleton connection to SQLite.
 *
 * ROLE IN THE APP:
 *   Every API route and Server Component imports `prisma` from here to query
 *   the database. This is the only place PrismaClient is instantiated.
 *
 * KEY PATTERNS:
 *   - Singleton on globalThis: survives Next.js hot-reload without new connections
 *   - PrismaBetterSqlite3 adapter: Prisma 6 driver-adapter for SQLite
 *   - Vercel workaround: copies dev.db → /tmp because serverless FS is read-only
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Why singleton? Each hot-reload would leak DB connections otherwise
 *   - Driver adapters decouple Prisma engine from native binary (edge-ready)
 *   - Production would typically use PostgreSQL + connection pooling (PgBouncer)
 */

import { PrismaClient } from "@/generated/prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import fs from "fs";
import path from "path";

// Store the client on globalThis so it survives hot-reloads in development
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient;
  dbReady: boolean;
};

/** Copy bundled SQLite DB to /tmp on Vercel's read-only filesystem. */
function prepareDatabaseFile(): string {
  if (globalForPrisma.dbReady) {
    return process.env.VERCEL
      ? "file:/tmp/dev.db"
      : process.env.DATABASE_URL ?? "file:./dev.db";
  }

  const bundledDb = path.join(process.cwd(), "dev.db");

  // Vercel serverless: copy bundled DB to writable /tmp on first request
  if (process.env.VERCEL) {
    const runtimeDb = path.join("/tmp", "dev.db");
    if (!fs.existsSync(runtimeDb) && fs.existsSync(bundledDb)) {
      fs.copyFileSync(bundledDb, runtimeDb);
    }
    globalForPrisma.dbReady = true;
    return `file:${runtimeDb}`;
  }

  globalForPrisma.dbReady = true;
  return process.env.DATABASE_URL ?? "file:./dev.db";
}

/** Instantiate PrismaClient with the Better-SQLite3 driver adapter. */
function createPrismaClient() {
  const url = prepareDatabaseFile();
  const adapter = new PrismaBetterSqlite3({ url });
  return new PrismaClient({
    adapter,
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });
}

// Reuse existing client or create a new one
export const prisma = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
