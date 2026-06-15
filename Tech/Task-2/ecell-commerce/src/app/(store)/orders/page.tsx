"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Package, ChevronRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { formatCurrency } from "@/lib/utils";
import type { Order } from "@/types";

const statusColors: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-700",
  CONFIRMED: "bg-blue-100 text-blue-700",
  PROCESSING: "bg-indigo-100 text-indigo-700",
  SHIPPED: "bg-purple-100 text-purple-700",
  DELIVERED: "bg-green-100 text-green-700",
  CANCELLED: "bg-red-100 text-red-700",
};

export default function OrdersPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/orders");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetch("/api/orders")
        .then((r) => r.json())
        .then(setOrders)
        .finally(() => setLoading(false));
    }
  }, [user]);

  if (authLoading || loading) {
    return <div className="p-20 text-center">Loading orders...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-zinc-900">My Orders</h1>
      <p className="mt-2 text-zinc-600">Track and manage your orders</p>

      {orders.length === 0 ? (
        <div className="mt-16 text-center">
          <Package className="mx-auto h-16 w-16 text-zinc-300" />
          <p className="mt-4 text-zinc-500">No orders yet.</p>
          <Link href="/shop" className="mt-4 inline-block text-indigo-600 hover:text-indigo-700">
            Start shopping
          </Link>
        </div>
      ) : (
        <div className="mt-10 space-y-4">
          {orders.map((order) => (
            <Link
              key={order.id}
              href={`/orders/${order.id}`}
              className="flex items-center justify-between rounded-2xl border border-zinc-200 bg-white p-6 transition hover:shadow-md"
            >
              <div>
                <p className="font-semibold text-zinc-900">{order.orderNumber}</p>
                <p className="mt-1 text-sm text-zinc-500">
                  {new Date(order.createdAt).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                  {" · "}
                  {order.items.length} item(s)
                </p>
                <span
                  className={`mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[order.status] || "bg-zinc-100"}`}
                >
                  {order.status}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-lg font-bold">{formatCurrency(order.total)}</span>
                <ChevronRight className="h-5 w-5 text-zinc-400" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
