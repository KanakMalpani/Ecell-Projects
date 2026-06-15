"use client";

import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import type { Coupon } from "@/types";

export default function AdminCouponsPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    code: "",
    type: "PERCENTAGE" as "PERCENTAGE" | "FIXED",
    value: "",
    minOrder: "0",
    expiresAt: "",
    maxUses: "",
  });

  const load = () => {
    fetch("/api/coupons").then((r) => r.json()).then(setCoupons);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch("/api/coupons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setShowForm(false);
    setForm({ code: "", type: "PERCENTAGE", value: "", minOrder: "0", expiresAt: "", maxUses: "" });
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Coupon Management</h1>
          <p className="text-zinc-600">Create and manage discount codes</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          New Coupon
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6">
          <div className="flex justify-between">
            <h2 className="font-semibold">Create Coupon</h2>
            <button type="button" onClick={() => setShowForm(false)}>
              <X className="h-5 w-5 text-zinc-400" />
            </button>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <input
              placeholder="Code (e.g. SAVE20)"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm uppercase"
            />
            <select
              value={form.type}
              onChange={(e) =>
                setForm({ ...form, type: e.target.value as "PERCENTAGE" | "FIXED" })
              }
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            >
              <option value="PERCENTAGE">Percentage</option>
              <option value="FIXED">Fixed Amount</option>
            </select>
            <input
              placeholder="Value"
              type="number"
              value={form.value}
              onChange={(e) => setForm({ ...form, value: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Min order amount"
              type="number"
              value={form.minOrder}
              onChange={(e) => setForm({ ...form, minOrder: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Expiry date"
              type="date"
              value={form.expiresAt}
              onChange={(e) => setForm({ ...form, expiresAt: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Max uses (optional)"
              type="number"
              value={form.maxUses}
              onChange={(e) => setForm({ ...form, maxUses: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            className="mt-4 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white"
          >
            Create Coupon
          </button>
        </form>
      )}

      <div className="mt-8 overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Code</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Type</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Value</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Used</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Expires</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {coupons.map((coupon) => (
              <tr key={coupon.id} className="border-b border-zinc-100">
                <td className="px-4 py-3 font-mono font-medium">{coupon.code}</td>
                <td className="px-4 py-3">{coupon.type}</td>
                <td className="px-4 py-3">
                  {coupon.type === "PERCENTAGE" ? `${coupon.value}%` : `₹${coupon.value}`}
                </td>
                <td className="px-4 py-3">
                  {coupon.usedCount}
                  {coupon.maxUses ? ` / ${coupon.maxUses}` : ""}
                </td>
                <td className="px-4 py-3">
                  {new Date(coupon.expiresAt).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      coupon.active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                    }`}
                  >
                    {coupon.active ? "Active" : "Inactive"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
