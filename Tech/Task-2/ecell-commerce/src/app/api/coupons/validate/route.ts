/**
 * Coupon Validation API — POST /api/coupons/validate
 *
 * ROLE IN THE APP:
 *   Pre-checkout coupon check. Returns discount amount if valid, or error reason.
 *   Called by checkout page before placing order (UX preview of savings).
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Validates: exists, active, not expired, minOrder met, usage limit not reached
 *   - PERCENTAGE: (subtotal * value) / 100; FIXED: min(value, subtotal)
 *   - Final coupon increment happens in POST /api/orders (not here)
 */

import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

/** POST — Validate a coupon code against the current cart subtotal. */
export async function POST(request: NextRequest) {
  const { code, subtotal } = await request.json();

  if (!code || subtotal === undefined) {
    return NextResponse.json({ error: "Code and subtotal required" }, { status: 400 });
  }

  const coupon = await prisma.coupon.findUnique({
    where: { code: code.toUpperCase() },
  });

  if (!coupon) {
    return NextResponse.json({ valid: false, error: "Invalid coupon code" });
  }

  if (!coupon.active) {
    return NextResponse.json({ valid: false, error: "Coupon is inactive" });
  }

  if (new Date() > coupon.expiresAt) {
    return NextResponse.json({ valid: false, error: "Coupon has expired" });
  }

  if (subtotal < coupon.minOrder) {
    return NextResponse.json({
      valid: false,
      error: `Minimum order of ₹${coupon.minOrder} required`,
    });
  }

  if (coupon.maxUses !== null && coupon.usedCount >= coupon.maxUses) {
    return NextResponse.json({ valid: false, error: "Coupon usage limit reached" });
  }

  const discount =
    coupon.type === "PERCENTAGE"
      ? (subtotal * coupon.value) / 100
      : Math.min(coupon.value, subtotal);

  return NextResponse.json({
    valid: true,
    coupon: {
      code: coupon.code,
      type: coupon.type,
      value: coupon.value,
    },
    discount,
  });
}
