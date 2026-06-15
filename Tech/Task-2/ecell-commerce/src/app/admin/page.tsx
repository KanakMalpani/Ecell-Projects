"use client";

import { useEffect, useState } from "react";
import { DollarSign, ShoppingBag, Users, TrendingUp, AlertTriangle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Analytics } from "@/types";

export default function AdminDashboard() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/analytics")
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading analytics...</div>;
  if (!data) return <div>Failed to load analytics</div>;

  const stats = [
    {
      label: "Total Revenue",
      value: formatCurrency(data.totalRevenue),
      icon: DollarSign,
      color: "bg-green-50 text-green-600",
    },
    {
      label: "Total Orders",
      value: data.totalOrders.toString(),
      icon: ShoppingBag,
      color: "bg-blue-50 text-blue-600",
    },
    {
      label: "Customers",
      value: data.totalCustomers.toString(),
      icon: Users,
      color: "bg-purple-50 text-purple-600",
    },
    {
      label: "Conversion Rate",
      value: `${data.conversionRate}%`,
      icon: TrendingUp,
      color: "bg-indigo-50 text-indigo-600",
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-900">Analytics Dashboard</h1>
      <p className="mt-1 text-zinc-600">Overview of your store performance</p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-zinc-200 bg-white p-6">
            <div className={`inline-flex rounded-lg p-2 ${stat.color}`}>
              <stat.icon className="h-5 w-5" />
            </div>
            <p className="mt-4 text-2xl font-bold text-zinc-900">{stat.value}</p>
            <p className="text-sm text-zinc-500">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-zinc-200 bg-white p-6">
          <h2 className="font-semibold text-zinc-900">Top Selling Products</h2>
          {data.topProducts.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-500">No sales data yet</p>
          ) : (
            <div className="mt-4 space-y-3">
              {data.topProducts.map((p, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{p.name}</span>
                  <div className="text-right">
                    <span className="font-semibold">{formatCurrency(p.revenue)}</span>
                    <span className="ml-2 text-zinc-400">({p.quantity} sold)</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-6">
          <h2 className="font-semibold text-zinc-900">Order Status Breakdown</h2>
          <div className="mt-4 space-y-2">
            {Object.entries(data.statusBreakdown).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between text-sm">
                <span className="capitalize text-zinc-600">{status.toLowerCase()}</span>
                <span className="font-semibold">{count}</span>
              </div>
            ))}
            {Object.keys(data.statusBreakdown).length === 0 && (
              <p className="text-sm text-zinc-500">No orders yet</p>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-6">
          <h2 className="font-semibold text-zinc-900">Recent Revenue (30 days)</h2>
          <p className="mt-4 text-3xl font-bold text-zinc-900">
            {formatCurrency(data.recentRevenue)}
          </p>
          <p className="mt-1 text-sm text-zinc-500">
            {data.paidOrders} paid orders out of {data.totalOrders} total
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-6">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="font-semibold text-zinc-900">Low Stock Alert</h2>
          </div>
          {data.lowStock.length === 0 ? (
            <p className="mt-4 text-sm text-green-600">All products well stocked</p>
          ) : (
            <div className="mt-4 space-y-2">
              {data.lowStock.map((p) => (
                <div key={p.id} className="flex justify-between text-sm">
                  <span>{p.name}</span>
                  <span className="font-semibold text-amber-600">{p.stock} left</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
