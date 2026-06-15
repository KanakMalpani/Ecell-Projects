"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Product, Category } from "@/types";

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    stock: "",
    imageUrl: "",
    categoryId: "",
    featured: false,
  });

  const load = () => {
    fetch("/api/products").then((r) => r.json()).then(setProducts);
    fetch("/api/categories").then((r) => r.json()).then(setCategories);
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setForm({
      name: "",
      description: "",
      price: "",
      stock: "",
      imageUrl: "",
      categoryId: categories[0]?.id || "",
      featured: false,
    });
    setEditingSlug(null);
    setShowForm(false);
  };

  const openEdit = (product: Product) => {
    setForm({
      name: product.name,
      description: product.description,
      price: product.price.toString(),
      stock: product.stock.toString(),
      imageUrl: product.imageUrl,
      categoryId: product.categoryId,
      featured: product.featured,
    });
    setEditingSlug(product.slug);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = editingSlug ? `/api/products/${editingSlug}` : "/api/products";
    const method = editingSlug ? "PUT" : "POST";

    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    resetForm();
    load();
  };

  const handleDelete = async (slug: string) => {
    if (!confirm("Delete this product?")) return;
    await fetch(`/api/products/${slug}`, { method: "DELETE" });
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Products</h1>
          <p className="text-zinc-600">{products.length} products in catalog</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true);
            setForm({ ...form, categoryId: categories[0]?.id || "" });
          }}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Add Product
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6"
        >
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">{editingSlug ? "Edit Product" : "New Product"}</h2>
            <button type="button" onClick={resetForm}>
              <X className="h-5 w-5 text-zinc-400" />
            </button>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <input
              placeholder="Product name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <select
              value={form.categoryId}
              onChange={(e) => setForm({ ...form, categoryId: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Price"
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Stock"
              type="number"
              value={form.stock}
              onChange={(e) => setForm({ ...form, stock: e.target.value })}
              required
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <input
              placeholder="Image URL"
              value={form.imageUrl}
              onChange={(e) => setForm({ ...form, imageUrl: e.target.value })}
              required
              className="col-span-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <textarea
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              required
              rows={3}
              className="col-span-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.featured}
                onChange={(e) => setForm({ ...form, featured: e.target.checked })}
              />
              Featured product
            </label>
          </div>
          <button
            type="submit"
            className="mt-4 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {editingSlug ? "Update" : "Create"}
          </button>
        </form>
      )}

      <div className="mt-8 overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Product</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Category</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Price</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600">Stock</th>
              <th className="px-4 py-3 text-right font-medium text-zinc-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id} className="border-b border-zinc-100">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="relative h-10 w-10 overflow-hidden rounded-lg">
                      <Image src={product.imageUrl} alt="" fill className="object-cover" />
                    </div>
                    <span className="font-medium">{product.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-zinc-600">{product.category?.name}</td>
                <td className="px-4 py-3">{formatCurrency(product.price)}</td>
                <td className="px-4 py-3">
                  <span className={product.stock <= 10 ? "text-amber-600 font-medium" : ""}>
                    {product.stock}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => openEdit(product)}
                    className="mr-2 rounded p-1 hover:bg-zinc-100"
                  >
                    <Pencil className="h-4 w-4 text-zinc-500" />
                  </button>
                  <button
                    onClick={() => handleDelete(product.slug)}
                    className="rounded p-1 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
