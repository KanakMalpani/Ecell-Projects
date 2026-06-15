/**
 * Prisma database client — connects the app to SQLite.
 *
 * Prisma is an ORM (Object-Relational Mapper) that lets you query the
 * database using TypeScript instead of raw SQL.
 *
 * This file creates a SINGLE shared PrismaClient instance (singleton pattern)
 * so Next.js hot-reload doesn't open a new DB connection on every refresh.
 *
 * On Vercel (serverless): copies dev.db to /tmp because the filesystem is read-only.
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

/** Resolve the SQLite database file path for local dev vs Vercel deployment. */
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
