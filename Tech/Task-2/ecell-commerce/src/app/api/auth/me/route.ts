/**
 * Current User API — GET /api/auth/me
 *
 * ROLE IN THE APP:
 *   Session restoration endpoint. AuthContext calls this on app mount to check
 *   if the httpOnly JWT cookie is still valid and return the user payload.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Returns { user: null } instead of 401 — client treats null as "not logged in"
 *   - getSession() reads cookie server-side; no token exposed to JavaScript
 */

import { NextResponse } from "next/server";
import { getSession } from "@/lib/auth";

/** GET — Return the currently authenticated user from the JWT cookie. */
export async function GET() {
  const user = await getSession();
  if (!user) {
    return NextResponse.json({ user: null });
  }
  return NextResponse.json({ user });
}
