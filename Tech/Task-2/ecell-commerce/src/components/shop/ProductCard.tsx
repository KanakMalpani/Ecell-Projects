"use client";

import Link from "next/link";
import Image from "next/image";
import { ShoppingBag } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";
import { useCart } from "@/context/CartContext";

export default function ProductCard({ product }: { product: Product }) {
  const { addItem } = useCart();

  return (
    <article className="group overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm transition hover:shadow-lg">
      <Link href={`/shop/${product.slug}`} className="relative block aspect-square overflow-hidden">
        <Image
          src={product.imageUrl}
          alt={product.name}
          fill
          className="object-cover transition duration-500 group-hover:scale-105"
          sizes="(max-width: 768px) 100vw, 25vw"
        />
        {product.stock <= 5 && product.stock > 0 && (
          <span className="absolute left-3 top-3 rounded-full bg-amber-500 px-2 py-0.5 text-xs font-medium text-white">
            Low stock
          </span>
        )}
        {product.stock === 0 && (
          <span className="absolute inset-0 flex items-center justify-center bg-black/50 text-sm font-semibold text-white">
            Out of stock
          </span>
        )}
      </Link>
      <div className="p-4">
        {product.category && (
          <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">
            {product.category.name}
          </p>
        )}
        <Link href={`/shop/${product.slug}`}>
          <h3 className="mt-1 line-clamp-2 font-semibold text-zinc-900 hover:text-indigo-600">
            {product.name}
          </h3>
        </Link>
        <div className="mt-3 flex items-center justify-between">
          <span className="text-lg font-bold text-zinc-900">{formatCurrency(product.price)}</span>
          <button
            disabled={product.stock === 0}
            onClick={() =>
              addItem({
                productId: product.id,
                name: product.name,
                price: product.price,
                imageUrl: product.imageUrl,
                slug: product.slug,
                stock: product.stock,
              })
            }
            className="flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <ShoppingBag className="h-4 w-4" />
            Add
          </button>
        </div>
      </div>
    </article>
  );
}
