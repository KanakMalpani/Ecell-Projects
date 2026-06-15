import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth";

export async function GET() {
  try {
    await requireAdmin();

    const orders = await prisma.order.findMany({
      include: { items: { include: { product: true } } },
    });

    const totalRevenue = orders
      .filter((o) => o.paymentStatus === "PAID")
      .reduce((sum, o) => sum + o.total, 0);

    const totalOrders = orders.length;
    const paidOrders = orders.filter((o) => o.paymentStatus === "PAID").length;
    const conversionRate = totalOrders > 0 ? (paidOrders / totalOrders) * 100 : 0;

    const productSales: Record<string, { name: string; quantity: number; revenue: number }> = {};
    for (const order of orders) {
      if (order.paymentStatus !== "PAID") continue;
      for (const item of order.items) {
        if (!productSales[item.productId]) {
          productSales[item.productId] = {
            name: item.product.name,
            quantity: 0,
            revenue: 0,
          };
        }
        productSales[item.productId].quantity += item.quantity;
        productSales[item.productId].revenue += item.price * item.quantity;
      }
    }

    const topProducts = Object.values(productSales)
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 5);

    const statusBreakdown = orders.reduce(
      (acc, o) => {
        acc[o.status] = (acc[o.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    const last30Days = new Date();
    last30Days.setDate(last30Days.getDate() - 30);
    const recentOrders = orders.filter((o) => o.createdAt >= last30Days);
    const recentRevenue = recentOrders
      .filter((o) => o.paymentStatus === "PAID")
      .reduce((sum, o) => sum + o.total, 0);

    const lowStock = await prisma.product.findMany({
      where: { stock: { lte: 10 } },
      select: { id: true, name: true, stock: true },
      orderBy: { stock: "asc" },
      take: 5,
    });

    const totalProducts = await prisma.product.count();
    const totalCustomers = await prisma.user.count({ where: { role: "USER" } });

    return NextResponse.json({
      totalRevenue,
      recentRevenue,
      totalOrders,
      paidOrders,
      conversionRate: Math.round(conversionRate * 10) / 10,
      topProducts,
      statusBreakdown,
      lowStock,
      totalProducts,
      totalCustomers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to fetch analytics";
    return NextResponse.json({ error: message }, { status: 403 });
  }
}
