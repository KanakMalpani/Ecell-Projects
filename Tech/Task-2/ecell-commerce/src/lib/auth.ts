import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import { cookies } from "next/headers";
import type { Role } from "@/generated/prisma/client";

const TOKEN_COOKIE = "ecell_token";

export type AuthUser = {
  id: string;
  email: string;
  name: string;
  role: Role;
};

function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET;
  if (secret) return secret;

  if (process.env.NODE_ENV === "production") {
    throw new Error("JWT_SECRET environment variable is required in production");
  }

  return "local-dev-only-secret-not-for-production";
}

export async function hashPassword(password: string) {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string) {
  return bcrypt.compare(password, hash);
}

export function signToken(user: AuthUser) {
  return jwt.sign(
    { id: user.id, email: user.email, name: user.name, role: user.role },
    getJwtSecret(),
    { expiresIn: "7d" }
  );
}

export function verifyToken(token: string): AuthUser | null {
  try {
    const payload = jwt.verify(token, getJwtSecret()) as AuthUser;
    return payload;
  } catch {
    return null;
  }
}

export async function getSession(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(TOKEN_COOKIE)?.value;
  if (!token) return null;
  return verifyToken(token);
}

export async function requireAuth(): Promise<AuthUser> {
  const user = await getSession();
  if (!user) throw new Error("Unauthorized");
  return user;
}

export async function requireAdmin(): Promise<AuthUser> {
  const user = await requireAuth();
  if (user.role !== "ADMIN") throw new Error("Forbidden");
  return user;
}

export { TOKEN_COOKIE };
