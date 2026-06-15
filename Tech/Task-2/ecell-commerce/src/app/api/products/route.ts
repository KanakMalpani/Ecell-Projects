import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";
import { slugify } from "@/lib/utils";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const search = searchParams.get("search");
  const featured = searchParams.get("featured");
  const minPrice = searchParams.get("minPrice");
  const maxPrice = searchParams.get("maxPrice");
  const sort = searchParams.get("sort") || "newest";

  const where: Record<string, unknown> = {};

  if (category) {
    where.category = { slug: category };
  }
  if (search) {
    where.OR = [
      { name: { contains: search } },
      { description: { contains: search } },
    ];
  }
  if (featured === "true") {
    where.featured = true;
  }
  if (minPrice || maxPrice) {
    where.price = {
      ...(minPrice ? { gte: parseFloat(minPrice) } : {}),
      ...(maxPrice ? { lte: parseFloat(maxPrice) } : {}),
    };
  }

  const orderBy =
    sort === "price-asc"
      ? { price: "asc" as const }
      : sort === "price-desc"
        ? { price: "desc" as const }
        : sort === "name"
          ? { name: "asc" as const }
          : { createdAt: "desc" as const };

  const products = await prisma.product.findMany({
    where,
    include: { category: true },
    orderBy,
  });

  return NextResponse.json(products);
}

export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();
    const slug = body.slug || slugify(body.name);

    const product = await prisma.product.create({
      data: {
        name: body.name,
        slug,
        description: body.description,
        price: parseFloat(body.price),
        stock: parseInt(body.stock, 10),
        imageUrl: body.imageUrl,
        featured: body.featured ?? false,
        categoryId: body.categoryId,
      },
      include: { category: true },
    });

    return NextResponse.json(product, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create product";
    const status = message === "Unauthorized" || message === "Forbidden" ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
