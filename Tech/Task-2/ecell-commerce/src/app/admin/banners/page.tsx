"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Plus, Trash2, X } from "lucide-react";

type Banner = {
  id: string;
  title: string;
  subtitle: string | null;
  imageUrl: string;
  link: string | null;
  active: boolean;
  startDate: string | null;
  endDate: string | null;
  sortOrder: number;
};

export default function AdminBannersPage() {
  const [banners, setBanners] = useState<Banner[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    subtitle: "",
    imageUrl: "",
    link: "",
    active: true,
    startDate: "",
    endDate: "",
    sortOrder: "0",
  });

  const load = async () => {
    const res = await fetch("/api/banners?all=true");
    const data = await res.json();
    setBanners(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch("/api/banners", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setShowForm(false);
    setForm({
      title: "",
      subtitle: "",
      imageUrl: "",
      link: "",
      active: true,
      startDate: "",
      endDate: "",
      sortOrder: "0",
    });
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this banner?")) return;
    await fetch(`/api/banners/${id}`, { method: "DELETE" });
    load();
  };

  const toggleActive = async (banner: Banner) => {
    await fetch(`/api/banners/${banner.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...banner, active: !banner.active }),
    });
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Banner Management</h1>
          <p className="text-zinc-600">Manage homepage promotional campaigns</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          New Banner
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6">
          <div className="flex justify-between">
            <h2 className="font-semibold">Create Banner</h2>
            <button type="button" onClick={() => setShowForm(false)}>
              <X className="h-5 w-5 text-zinc-400" />
            </button>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <input
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Subtitle"
              value={form.subtitle}
              onChange={(e) => setForm({ ...form, subtitle: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Image URL"
              value={form.imageUrl}
              onChange={(e) => setForm({ ...form, imageUrl: e.target.value })}
              required
              className="col-span-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Link URL (e.g. /shop)"
              value={form.link}
              onChange={(e) => setForm({ ...form, link: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Sort order"
              type="number"
              value={form.sortOrder}
              onChange={(e) => setForm({ ...form, sortOrder: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Start date (optional)"
              type="date"
              value={form.startDate}
              onChange={(e) => setForm({ ...form, startDate: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="End date (optional)"
              type="date"
              value={form.endDate}
              onChange={(e) => setForm({ ...form, endDate: e.target.value })}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            className="mt-4 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white"
          >
            Create Banner
          </button>
        </form>
      )}

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {banners.map((banner) => (
          <div key={banner.id} className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
            <div className="relative aspect-[2/1]">
              <Image src={banner.imageUrl} alt={banner.title} fill className="object-cover" />
            </div>
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{banner.title}</h3>
                  {banner.subtitle && (
                    <p className="text-sm text-zinc-500">{banner.subtitle}</p>
                  )}
                </div>
                <button
                  onClick={() => toggleActive(banner)}
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    banner.active ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
                  }`}
                >
                  {banner.active ? "Active" : "Inactive"}
                </button>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => handleDelete(banner.id)}
                  className="flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="h-3 w-3" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
