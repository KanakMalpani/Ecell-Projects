"use client";

import Image from "next/image";
import Link from "next/link";
import { Minus, Plus, Trash2, ShoppingBag } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { formatCurrency } from "@/lib/utils";

export default function CartPage() {
  const { items, updateQuantity, removeItem, subtotal, totalItems } = useCart();

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6 lg:px-8">
        <ShoppingBag className="mx-auto h-16 w-16 text-zinc-300" />
        <h1 className="mt-6 text-2xl font-bold text-zinc-900">Your cart is empty</h1>
        <p className="mt-2 text-zinc-600">Add some products to get started.</p>
        <Link
          href="/shop"
          className="mt-8 inline-block rounded-xl bg-indigo-600 px-8 py-3 font-semibold text-white hover:bg-indigo-700"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-zinc-900">Shopping Cart</h1>
      <p className="mt-2 text-zinc-600">{totalItems} item(s) in your cart</p>

      <div className="mt-10 grid gap-10 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {items.map((item) => (
            <div
              key={item.productId}
              className="flex gap-4 rounded-2xl border border-zinc-200 bg-white p-4"
            >
              <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-lg">
                <Image src={item.imageUrl} alt={item.name} fill className="object-cover" />
              </div>
              <div className="flex flex-1 flex-col justify-between">
                <div>
                  <Link
                    href={`/shop/${item.slug}`}
                    className="font-semibold text-zinc-900 hover:text-indigo-600"
                  >
                    {item.name}
                  </Link>
                  <p className="text-sm text-zinc-500">{formatCurrency(item.price)} each</p>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center rounded-lg border border-zinc-200">
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                      className="p-2 hover:bg-zinc-50"
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                    <span className="w-10 text-center text-sm font-medium">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                      className="p-2 hover:bg-zinc-50"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-semibold">
                      {formatCurrency(item.price * item.quantity)}
                    </span>
                    <button
                      onClick={() => removeItem(item.productId)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="h-fit rounded-2xl border border-zinc-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-zinc-900">Order Summary</h2>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-zinc-600">Subtotal</span>
              <span className="font-medium">{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-600">Shipping</span>
              <span className="font-medium">{subtotal >= 999 ? "Free" : formatCurrency(99)}</span>
            </div>
          </div>
          <div className="mt-4 flex justify-between border-t border-zinc-200 pt-4">
            <span className="font-semibold">Total</span>
            <span className="text-xl font-bold">
              {formatCurrency(subtotal + (subtotal >= 999 ? 0 : 99))}
            </span>
          </div>
          <Link
            href="/checkout"
            className="mt-6 block w-full rounded-xl bg-indigo-600 py-3 text-center font-semibold text-white hover:bg-indigo-700"
          >
            Proceed to Checkout
          </Link>
        </div>
      </div>
    </div>
  );
}
