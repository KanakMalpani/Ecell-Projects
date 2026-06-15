import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

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
