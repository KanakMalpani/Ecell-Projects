/**
 * Categories API — /api/categories
 *
 * ROLE IN THE APP:
 *   Lists product categories with product counts for shop sidebar filters.
 *   Admin can create new categories via POST.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - _count: { select: { products: true } } is Prisma's aggregation shortcut
 *   - Categories linked to products via foreign key (categoryId on Product)
 */

import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";
import { slugify } from "@/lib/utils";
import { NextRequest } from "next/server";

/** GET — List all categories with product counts (public). */
export async function GET() {
  const categories = await prisma.category.findMany({
    include: { _count: { select: { products: true } } },
    orderBy: { name: "asc" },
  });
  return NextResponse.json(categories);
}

/** POST — Admin only: create a new product category. */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();
    const slug = body.slug || slugify(body.name);

    const category = await prisma.category.create({
      data: { name: body.name, slug },
    });

    return NextResponse.json(category, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create category";
    return NextResponse.json({ error: message }, { status: 403 });
  }
}
