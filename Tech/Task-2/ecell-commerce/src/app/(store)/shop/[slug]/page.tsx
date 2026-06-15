"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Minus, Plus, ShoppingBag, ArrowLeft } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { useCart } from "@/context/CartContext";
import type { Product } from "@/types";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();

  useEffect(() => {
    fetch(`/api/products/${slug}`)
      .then((r) => r.json())
      .then(setProduct)
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return <div className="p-20 text-center text-zinc-500">Loading...</div>;
  }

  if (!product) {
    return (
      <div className="p-20 text-center">
        <p className="text-zinc-500">Product not found.</p>
        <Link href="/shop" className="mt-4 inline-block text-indigo-600">
          Back to shop
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Link
        href="/shop"
        className="mb-6 inline-flex items-center gap-1 text-sm text-zinc-600 hover:text-indigo-600"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to shop
      </Link>

      <div className="grid gap-10 lg:grid-cols-2">
        <div className="relative aspect-square overflow-hidden rounded-2xl bg-zinc-100">
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover"
            priority
            sizes="(max-width: 1024px) 100vw, 50vw"
          />
        </div>

        <div>
          {product.category && (
            <p className="text-sm font-medium uppercase tracking-wide text-indigo-600">
              {product.category.name}
            </p>
          )}
          <h1 className="mt-2 text-3xl font-bold text-zinc-900">{product.name}</h1>
          <p className="mt-4 text-3xl font-bold text-zinc-900">{formatCurrency(product.price)}</p>

          <p className="mt-6 leading-relaxed text-zinc-600">{product.description}</p>

          <div className="mt-6 flex items-center gap-2">
            <span
              className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                product.stock > 10
                  ? "bg-green-100 text-green-700"
                  : product.stock > 0
                    ? "bg-amber-100 text-amber-700"
                    : "bg-red-100 text-red-700"
              }`}
            >
              {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
            </span>
          </div>

          {product.stock > 0 && (
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <div className="flex items-center rounded-lg border border-zinc-200">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="p-3 text-zinc-600 hover:bg-zinc-50"
                >
                  <Minus className="h-4 w-4" />
                </button>
                <span className="w-12 text-center font-medium">{quantity}</span>
                <button
                  onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                  className="p-3 text-zinc-600 hover:bg-zinc-50"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>

              <button
                onClick={() =>
                  addItem(
                    {
                      productId: product.id,
                      name: product.name,
                      price: product.price,
                      imageUrl: product.imageUrl,
                      slug: product.slug,
                      stock: product.stock,
                    },
                    quantity
                  )
                }
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-3 font-semibold text-white transition hover:bg-indigo-700"
              >
                <ShoppingBag className="h-5 w-5" />
                Add to Cart
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
