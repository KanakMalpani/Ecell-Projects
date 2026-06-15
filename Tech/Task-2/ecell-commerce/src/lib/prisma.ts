import { PrismaClient } from "@/generated/prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import fs from "fs";
import path from "path";

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient;
  dbReady: boolean;
};

function prepareDatabaseFile(): string {
  if (globalForPrisma.dbReady) {
    return process.env.VERCEL
      ? "file:/tmp/dev.db"
      : process.env.DATABASE_URL ?? "file:./dev.db";
  }

  const bundledDb = path.join(process.cwd(), "dev.db");

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

export const prisma = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
