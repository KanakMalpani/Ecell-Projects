/**
 * Coupons API — /api/coupons
 *
 * ROLE IN THE APP:
 *   Admin-only coupon CRUD. Codes are stored uppercase and validated at checkout.
 *   Supports PERCENTAGE (e.g. 10% off) and FIXED (e.g. ₹200 off) discount types.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - minOrder, expiresAt, maxUses, usedCount form a complete coupon validation chain
 *   - Actual discount calculation happens in /api/coupons/validate and POST /api/orders
 */
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

/** GET — Admin only: list all discount coupons. */
export async function GET() {
  try {
    await requireAdmin();
    const coupons = await prisma.coupon.findMany({ orderBy: { createdAt: "desc" } });
    return NextResponse.json(coupons);
  } catch {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
}

/** POST — Admin only: create a new discount coupon. */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();

    const coupon = await prisma.coupon.create({
      data: {
        code: body.code.toUpperCase(),
        type: body.type,
        value: parseFloat(body.value),
        minOrder: parseFloat(body.minOrder || 0),
        expiresAt: new Date(body.expiresAt),
        active: body.active ?? true,
        maxUses: body.maxUses ? parseInt(body.maxUses, 10) : null,
      },
    });

    return NextResponse.json(coupon, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create coupon" }, { status: 403 });
  }
}
