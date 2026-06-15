import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await requireAdmin();
    const { id } = await params;
    const body = await request.json();

    const banner = await prisma.banner.update({
      where: { id },
      data: {
        title: body.title,
        subtitle: body.subtitle,
        imageUrl: body.imageUrl,
        link: body.link,
        active: body.active,
        startDate: body.startDate ? new Date(body.startDate) : null,
        endDate: body.endDate ? new Date(body.endDate) : null,
        sortOrder: body.sortOrder,
      },
    });

    return NextResponse.json(banner);
  } catch {
    return NextResponse.json({ error: "Failed to update banner" }, { status: 403 });
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await requireAdmin();
    const { id } = await params;
    await prisma.banner.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Failed to delete banner" }, { status: 403 });
  }
}
