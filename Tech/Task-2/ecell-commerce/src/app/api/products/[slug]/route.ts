/**
 * Single Product API — /api/products/[slug]
 *
 * ROLE IN THE APP:
 *   Product detail lookup by URL slug (not ID — SEO-friendly URLs).
 *   Admin update/delete operations for catalog management.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Dynamic route params are Promise<{slug}> in Next.js 15 App Router
 *   - Slug-based routing: /shop/wireless-headphones maps to this API
 *   - include: { category: true } joins category data in one query
 */

import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

/** GET — Fetch a single product by slug (public). */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;
  const product = await prisma.product.findUnique({
    where: { slug },
    include: { category: true },
  });

  if (!product) {
    return NextResponse.json({ error: "Product not found" }, { status: 404 });
  }

  return NextResponse.json(product);
}

/** PUT — Admin only: update product fields by slug. */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    await requireAdmin();
    const { slug } = await params;
    const body = await request.json();

    const product = await prisma.product.update({
      where: { slug },
      data: {
        name: body.name,
        description: body.description,
        price: body.price !== undefined ? parseFloat(body.price) : undefined,
        stock: body.stock !== undefined ? parseInt(body.stock, 10) : undefined,
        imageUrl: body.imageUrl,
        featured: body.featured,
        categoryId: body.categoryId,
      },
      include: { category: true },
    });

    return NextResponse.json(product);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to update product";
    const status = message === "Unauthorized" || message === "Forbidden" ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}

/** DELETE — Admin only: remove product from catalog. */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    await requireAdmin();
    const { slug } = await params;
    await prisma.product.delete({ where: { slug } });
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to delete product";
    const status = message === "Unauthorized" || message === "Forbidden" ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
