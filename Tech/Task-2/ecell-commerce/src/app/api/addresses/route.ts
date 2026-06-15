import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth } from "@/lib/auth";

export async function GET() {
  try {
    const user = await requireAuth();
    const addresses = await prisma.address.findMany({
      where: { userId: user.id },
      orderBy: { isDefault: "desc" },
    });
    return NextResponse.json(addresses);
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth();
    const body = await request.json();

    if (body.isDefault) {
      await prisma.address.updateMany({
        where: { userId: user.id },
        data: { isDefault: false },
      });
    }

    const address = await prisma.address.create({
      data: {
        userId: user.id,
        label: body.label || "Home",
        street: body.street,
        city: body.city,
        state: body.state,
        zipCode: body.zipCode,
        country: body.country || "India",
        isDefault: body.isDefault ?? false,
      },
    });

    return NextResponse.json(address, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Failed to create address" }, { status: 401 });
  }
}
