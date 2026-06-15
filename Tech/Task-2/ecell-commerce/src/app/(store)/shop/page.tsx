"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import ProductCard from "@/components/shop/ProductCard";
import type { Product, Category } from "@/types";
import { Search } from "lucide-react";

function ShopContent() {
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [category, setCategory] = useState(searchParams.get("category") || "");
  const [sort, setSort] = useState("newest");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  useEffect(() => {
    fetch("/api/categories")
      .then((r) => r.json())
      .then(setCategories)
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (search) params.set("search", search);
    if (sort) params.set("sort", sort);
    if (minPrice) params.set("minPrice", minPrice);
    if (maxPrice) params.set("maxPrice", maxPrice);

    fetch(`/api/products?${params}`)
      .then((r) => r.json())
      .then(setProducts)
      .finally(() => setLoading(false));
  }, [category, search, sort, minPrice, maxPrice]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900">Shop</h1>
        <p className="mt-2 text-zinc-600">Browse our full catalog of products</p>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row">
        <aside className="w-full shrink-0 lg:w-64">
          <div className="rounded-2xl border border-zinc-200 bg-white p-6">
            <h2 className="font-semibold text-zinc-900">Filters</h2>

            <div className="mt-4">
              <label className="text-sm font-medium text-zinc-700">Search</label>
              <div className="relative mt-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search products..."
                  className="w-full rounded-lg border border-zinc-200 py-2 pl-10 pr-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="text-sm font-medium text-zinc-700">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              >
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name} {c._count ? `(${c._count.products})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <div>
                <label className="text-sm font-medium text-zinc-700">Min price</label>
                <input
                  type="number"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-700">Max price</label>
                <input
                  type="number"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                  placeholder="10000"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="text-sm font-medium text-zinc-700">Sort by</label>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
              >
                <option value="newest">Newest</option>
                <option value="price-asc">Price: Low to High</option>
                <option value="price-desc">Price: High to Low</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>
        </aside>

        <div className="flex-1">
          {loading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="aspect-square animate-pulse rounded-2xl bg-zinc-200" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <p className="text-center text-zinc-500 py-20">No products found.</p>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ShopPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center">Loading shop...</div>}>
      <ShopContent />
    </Suspense>
  );
}
