import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSession, requireAdmin } from "@/lib/auth";
import { generateOrderNumber } from "@/lib/utils";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const isAdmin = session.role === "ADMIN";
  const orders = await prisma.order.findMany({
    where: isAdmin ? {} : { userId: session.id },
    include: {
      items: { include: { product: true } },
      user: isAdmin ? { select: { name: true, email: true } } : false,
    },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(orders);
}

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session) {
      return NextResponse.json({ error: "Please login to checkout" }, { status: 401 });
    }

    const body = await request.json();
    const { items, shipping, couponCode, paymentMethod } = body;

    if (!items?.length) {
      return NextResponse.json({ error: "Cart is empty" }, { status: 400 });
    }

    const productIds = items.map((i: { productId: string }) => i.productId);
    const products = await prisma.product.findMany({
      where: { id: { in: productIds } },
    });

    let subtotal = 0;
    const orderItems: { productId: string; quantity: number; price: number }[] = [];

    for (const item of items) {
      const product = products.find((p) => p.id === item.productId);
      if (!product) {
        return NextResponse.json({ error: `Product not found` }, { status: 400 });
      }
      if (product.stock < item.quantity) {
        return NextResponse.json(
          { error: `Insufficient stock for ${product.name}` },
          { status: 400 }
        );
      }
      const lineTotal = product.price * item.quantity;
      subtotal += lineTotal;
      orderItems.push({
        productId: product.id,
        quantity: item.quantity,
        price: product.price,
      });
    }

    let discount = 0;
    let appliedCoupon: string | null = null;

    if (couponCode) {
      const coupon = await prisma.coupon.findUnique({
        where: { code: couponCode.toUpperCase() },
      });

      if (
        coupon &&
        coupon.active &&
        new Date() <= coupon.expiresAt &&
        subtotal >= coupon.minOrder &&
        (coupon.maxUses === null || coupon.usedCount < coupon.maxUses)
      ) {
        discount =
          coupon.type === "PERCENTAGE"
            ? (subtotal * coupon.value) / 100
            : Math.min(coupon.value, subtotal);
        appliedCoupon = coupon.code;

        await prisma.coupon.update({
          where: { id: coupon.id },
          data: { usedCount: { increment: 1 } },
        });
      }
    }

    const total = Math.max(0, subtotal - discount);

    const paymentStatus =
      paymentMethod === "simulated" ? ("PAID" as const) : ("PENDING" as const);
    const status = paymentStatus === "PAID" ? ("CONFIRMED" as const) : ("PENDING" as const);

    const order = await prisma.$transaction(async (tx) => {
      for (const item of orderItems) {
        await tx.product.update({
          where: { id: item.productId },
          data: { stock: { decrement: item.quantity } },
        });
      }

      return tx.order.create({
        data: {
          orderNumber: generateOrderNumber(),
          userId: session.id,
          status,
          paymentStatus,
          subtotal,
          discount,
          total,
          couponCode: appliedCoupon,
          shippingStreet: shipping.street,
          shippingCity: shipping.city,
          shippingState: shipping.state,
          shippingZip: shipping.zipCode,
          shippingCountry: shipping.country || "India",
          items: { create: orderItems },
        },
        include: { items: { include: { product: true } } },
      });
    });

    return NextResponse.json(order, { status: 201 });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Failed to create order" }, { status: 500 });
  }
}
