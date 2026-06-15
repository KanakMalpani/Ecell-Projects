import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";
import { isBannerActive } from "@/lib/utils";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const all = searchParams.get("all") === "true";

  if (all) {
    try {
      await requireAdmin();
      const banners = await prisma.banner.findMany({ orderBy: { sortOrder: "asc" } });
      return NextResponse.json(banners);
    } catch {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
  }

  const banners = await prisma.banner.findMany({ orderBy: { sortOrder: "asc" } });
  const active = banners.filter(isBannerActive);
  return NextResponse.json(active);
}

export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();

    const banner = await prisma.banner.create({
      data: {
        title: body.title,
        subtitle: body.subtitle,
        imageUrl: body.imageUrl,
        link: body.link,
        active: body.active ?? true,
        startDate: body.startDate ? new Date(body.startDate) : null,
        endDate: body.endDate ? new Date(body.endDate) : null,
        sortOrder: body.sortOrder ? parseInt(body.sortOrder, 10) : 0,
      },
    });

    return NextResponse.json(banner, { status: 201 });
  } catch {
    return NextResponse.json({ error: "Failed to create banner" }, { status: 403 });
  }
}
