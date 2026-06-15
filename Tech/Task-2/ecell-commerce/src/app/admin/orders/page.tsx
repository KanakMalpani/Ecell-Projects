"use client";

import { useEffect, useState } from "react";
import { formatCurrency } from "@/lib/utils";
import type { Order } from "@/types";

const statuses = ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    fetch("/api/orders")
      .then((r) => r.json())
      .then(setOrders)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const updateStatus = async (id: string, status: string) => {
    await fetch(`/api/orders/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    load();
  };

  if (loading) return <div>Loading orders...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-900">Order Management</h1>
      <p className="mt-1 text-zinc-600">{orders.length} total orders</p>

      <div className="mt-8 space-y-4">
        {orders.length === 0 ? (
          <p className="text-zinc-500">No orders yet.</p>
        ) : (
          orders.map((order) => (
            <div key={order.id} className="rounded-2xl border border-zinc-200 bg-white p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-zinc-900">{order.orderNumber}</p>
                  <p className="text-sm text-zinc-500">
                    {order.user?.name} ({order.user?.email}) ·{" "}
                    {new Date(order.createdAt).toLocaleDateString()}
                  </p>
                  <p className="mt-1 text-sm">
                    {order.items.length} items · {formatCurrency(order.total)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={order.status}
                    onChange={(e) => updateStatus(order.id, e.target.value)}
                    className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm"
                  >
                    {statuses.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {order.items.map((item) => (
                  <span
                    key={item.id}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-600"
                  >
                    {item.product.name} x{item.quantity}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
