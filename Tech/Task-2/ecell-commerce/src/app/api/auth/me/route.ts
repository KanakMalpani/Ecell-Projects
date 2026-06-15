/**
 * Current user API — check who is logged in.
 *
 * GET /api/auth/me → { user: { id, email, name, role } } or { user: null }
 *
 * Called by AuthContext on page load to restore the session.
 */
import { NextResponse } from "next/server";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) {
    return NextResponse.json({ user: null });
  }
  return NextResponse.json({ user });
}
