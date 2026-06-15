"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, Truck, CheckCircle2, Circle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Order } from "@/types";

const trackingSteps = ["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"];

export default function OrderDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/orders/${id}`)
      .then((r) => r.json())
      .then(setOrder)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-20 text-center">Loading...</div>;
  if (!order) {
    return (
      <div className="p-20 text-center">
        <p>Order not found.</p>
        <Link href="/orders" className="text-indigo-600">
          Back to orders
        </Link>
      </div>
    );
  }

  const currentStepIndex = trackingSteps.indexOf(order.status);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <Link
        href="/orders"
        className="inline-flex items-center gap-1 text-sm text-zinc-600 hover:text-indigo-600"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to orders
      </Link>

      <div className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">{order.orderNumber}</h1>
            <p className="mt-1 text-sm text-zinc-500">
              Placed on{" "}
              {new Date(order.createdAt).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>
          </div>
          <span className="rounded-full bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700">
            {order.status}
          </span>
        </div>

        {/* Order tracking */}
        {order.status !== "CANCELLED" && (
          <div className="mt-8">
            <div className="flex items-center gap-2">
              <Truck className="h-5 w-5 text-indigo-600" />
              <h2 className="font-semibold">Order Tracking</h2>
            </div>
            <div className="mt-6 flex justify-between">
              {trackingSteps.map((step, i) => {
                const completed = currentStepIndex >= i;
                return (
                  <div key={step} className="flex flex-1 flex-col items-center">
                    {completed ? (
                      <CheckCircle2 className="h-6 w-6 text-indigo-600" />
                    ) : (
                      <Circle className="h-6 w-6 text-zinc-300" />
                    )}
                    <span
                      className={`mt-2 text-xs font-medium ${completed ? "text-indigo-600" : "text-zinc-400"}`}
                    >
                      {step.charAt(0) + step.slice(1).toLowerCase()}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-8 border-t border-zinc-200 pt-6">
          <h2 className="font-semibold">Items</h2>
          <div className="mt-4 space-y-4">
            {order.items.map((item) => (
              <div key={item.id} className="flex gap-4">
                <div className="relative h-16 w-16 overflow-hidden rounded-lg">
                  <Image
                    src={item.product.imageUrl}
                    alt={item.product.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex-1">
                  <p className="font-medium">{item.product.name}</p>
                  <p className="text-sm text-zinc-500">
                    Qty: {item.quantity} · {formatCurrency(item.price)} each
                  </p>
                </div>
                <p className="font-semibold">{formatCurrency(item.price * item.quantity)}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 border-t border-zinc-200 pt-6">
          <h2 className="font-semibold">Shipping Address</h2>
          <p className="mt-2 text-sm text-zinc-600">
            {order.shippingStreet}, {order.shippingCity}, {order.shippingState}{" "}
            {order.shippingZip}, {order.shippingCountry}
          </p>
        </div>

        <div className="mt-6 space-y-2 border-t border-zinc-200 pt-6 text-sm">
          <div className="flex justify-between">
            <span className="text-zinc-600">Subtotal</span>
            <span>{formatCurrency(order.subtotal)}</span>
          </div>
          {order.discount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount {order.couponCode && `(${order.couponCode})`}</span>
              <span>-{formatCurrency(order.discount)}</span>
            </div>
          )}
          <div className="flex justify-between font-bold text-base">
            <span>Total</span>
            <span>{formatCurrency(order.total)}</span>
          </div>
          <div className="flex justify-between text-zinc-500">
            <span>Payment</span>
            <span>{order.paymentStatus}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
