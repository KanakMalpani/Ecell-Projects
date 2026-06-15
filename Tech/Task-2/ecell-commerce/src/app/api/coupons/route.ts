import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

export async function GET() {
  try {
    await requireAdmin();
    const coupons = await prisma.coupon.findMany({ orderBy: { createdAt: "desc" } });
    return NextResponse.json(coupons);
  } catch {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
}

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
