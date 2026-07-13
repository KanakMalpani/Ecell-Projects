/**
 * Authentication helpers — JWT tokens, password hashing, session management.
 *
 * ROLE IN THE APP:
 *   Central auth module used by API routes (requireAuth/requireAdmin) and
 *   client session restore (/api/auth/me → getSession). Implements the
 *   server-side half of JWT auth; the client half lives in AuthContext.
 *
 * AUTH FLOW:
 *   Register/Login → server hashes password → signs JWT → stores in httpOnly cookie
 *   Protected pages → read cookie → verify JWT → get user info
 *
 * KEY FUNCTIONS:
 *   hashPassword / verifyPassword — bcrypt (cost factor 10) for password security
 *   signToken / verifyToken       — JWT create and validate (7-day expiry)
 *   getSession                    — read current user from cookie (server-side)
 *   requireAuth / requireAdmin    — guard API routes; throw if unauthorized
 *
 * PI INTERVIEW TALKING POINTS:
 *   - httpOnly cookie prevents XSS from stealing the JWT (JS can't read it)
 *   - bcrypt is slow by design → mitigates brute-force on stolen DB dumps
 *   - requireAdmin enforces RBAC: USER vs ADMIN roles from Prisma enum
 *   - Dev fallback JWT secret is blocked in production (fail-fast security)
 */

import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import { cookies } from "next/headers";
import type { Role } from "@/generated/prisma/client";

const TOKEN_COOKIE = "ecell_token";

/** Shape of the authenticated user stored in the JWT payload. */
export type AuthUser = {
  id: string;
  email: string;
  name: string;
  role: Role;  // "USER" or "ADMIN"
};

/** Resolve JWT signing secret; throws in production if JWT_SECRET is missing. */
function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET;
  if (secret) return secret;

  // In production, JWT_SECRET must be set — never use the dev fallback
  if (process.env.NODE_ENV === "production") {
    throw new Error("JWT_SECRET environment variable is required in production");
  }

  return "local-dev-only-secret-not-for-production";
}

/** Hash a plain-text password before storing in the database. */
export async function hashPassword(password: string) {
  return bcrypt.hash(password, 10);
}

/** Compare a login password against the stored hash. */
export async function verifyPassword(password: string, hash: string) {
  return bcrypt.compare(password, hash);
}

/** Create a signed JWT token valid for 7 days. */
export function signToken(user: AuthUser) {
  return jwt.sign(
    { id: user.id, email: user.email, name: user.name, role: user.role },
    getJwtSecret(),
    { expiresIn: "7d" }
  );
}

/** Decode and verify a JWT. Returns null if expired or tampered. */
export function verifyToken(token: string): AuthUser | null {
  try {
    const payload = jwt.verify(token, getJwtSecret()) as AuthUser;
    return payload;
  } catch {
    return null;
  }
}

/** Read the current logged-in user from the auth cookie (server components / API routes). */
export async function getSession(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(TOKEN_COOKIE)?.value;
  if (!token) return null;
  return verifyToken(token);
}

/** Like getSession but throws "Unauthorized" if not logged in. */
export async function requireAuth(): Promise<AuthUser> {
  const user = await getSession();
  if (!user) throw new Error("Unauthorized");
  return user;
}

/** Like requireAuth but also checks role === "ADMIN". */
export async function requireAdmin(): Promise<AuthUser> {
  const user = await requireAuth();
  if (user.role !== "ADMIN") throw new Error("Forbidden");
  return user;
}

export { TOKEN_COOKIE };
