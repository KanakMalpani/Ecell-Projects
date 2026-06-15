"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CreditCard, MapPin, Tag, CheckCircle } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { formatCurrency } from "@/lib/utils";
import type { Address } from "@/types";

export default function CheckoutPage() {
  const { items, subtotal, clearCart } = useCart();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [addresses, setAddresses] = useState<Address[]>([]);
  const [couponCode, setCouponCode] = useState("");
  const [discount, setDiscount] = useState(0);
  const [couponError, setCouponError] = useState("");
  const [couponApplied, setCouponApplied] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [orderComplete, setOrderComplete] = useState<{ orderNumber: string; id: string } | null>(
    null
  );

  const [shipping, setShipping] = useState({
    street: "",
    city: "",
    state: "",
    zipCode: "",
    country: "India",
  });

  const shippingCost = subtotal >= 999 ? 0 : 99;
  const total = Math.max(0, subtotal + shippingCost - discount);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/checkout");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetch("/api/addresses")
        .then((r) => r.json())
        .then((data) => {
          if (Array.isArray(data)) {
            setAddresses(data);
            const defaultAddr = data.find((a: Address) => a.isDefault) || data[0];
            if (defaultAddr) {
              setShipping({
                street: defaultAddr.street,
                city: defaultAddr.city,
                state: defaultAddr.state,
                zipCode: defaultAddr.zipCode,
                country: defaultAddr.country,
              });
            }
          }
        })
        .catch(() => {});
    }
  }, [user]);

  const applyCoupon = async () => {
    setCouponError("");
    const res = await fetch("/api/coupons/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: couponCode, subtotal }),
    });
    const data = await res.json();
    if (data.valid) {
      setDiscount(data.discount);
      setCouponApplied(true);
    } else {
      setCouponError(data.error || "Invalid coupon");
      setDiscount(0);
      setCouponApplied(false);
    }
  };

  const placeOrder = async () => {
    if (!shipping.street || !shipping.city || !shipping.state || !shipping.zipCode) {
      alert("Please fill in all shipping details");
      return;
    }

    setProcessing(true);
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: items.map((i) => ({ productId: i.productId, quantity: i.quantity })),
          shipping,
          couponCode: couponApplied ? couponCode : undefined,
          paymentMethod: "simulated",
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      clearCart();
      setOrderComplete({ orderNumber: data.orderNumber, id: data.id });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setProcessing(false);
    }
  };

  if (authLoading) return <div className="p-20 text-center">Loading...</div>;

  if (items.length === 0 && !orderComplete) {
    return (
      <div className="p-20 text-center">
        <p>Your cart is empty.</p>
        <Link href="/shop" className="mt-4 inline-block text-indigo-600">
          Continue shopping
        </Link>
      </div>
    );
  }

  if (orderComplete) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
        <h1 className="mt-6 text-2xl font-bold text-zinc-900">Order Confirmed!</h1>
        <p className="mt-2 text-zinc-600">
          Thank you for your purchase. Your order number is:
        </p>
        <p className="mt-2 text-xl font-bold text-indigo-600">{orderComplete.orderNumber}</p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href={`/orders/${orderComplete.id}`}
            className="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700"
          >
            Track Order
          </Link>
          <Link
            href="/shop"
            className="rounded-xl border border-zinc-200 px-6 py-3 font-semibold hover:bg-zinc-50"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-zinc-900">Checkout</h1>

      <div className="mt-10 grid gap-10 lg:grid-cols-3">
        <div className="space-y-8 lg:col-span-2">
          {/* Shipping */}
          <section className="rounded-2xl border border-zinc-200 bg-white p-6">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold">Shipping Address</h2>
            </div>

            {addresses.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {addresses.map((addr) => (
                  <button
                    key={addr.id}
                    onClick={() =>
                      setShipping({
                        street: addr.street,
                        city: addr.city,
                        state: addr.state,
                        zipCode: addr.zipCode,
                        country: addr.country,
                      })
                    }
                    className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs hover:border-indigo-500"
                  >
                    {addr.label}: {addr.city}
                  </button>
                ))}
              </div>
            )}

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <input
                placeholder="Street address"
                value={shipping.street}
                onChange={(e) => setShipping({ ...shipping, street: e.target.value })}
                className="col-span-2 rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none sm:col-span-2"
              />
              <input
                placeholder="City"
                value={shipping.city}
                onChange={(e) => setShipping({ ...shipping, city: e.target.value })}
                className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
              <input
                placeholder="State"
                value={shipping.state}
                onChange={(e) => setShipping({ ...shipping, state: e.target.value })}
                className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
              <input
                placeholder="ZIP Code"
                value={shipping.zipCode}
                onChange={(e) => setShipping({ ...shipping, zipCode: e.target.value })}
                className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
              <input
                placeholder="Country"
                value={shipping.country}
                onChange={(e) => setShipping({ ...shipping, country: e.target.value })}
                className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </section>

          {/* Coupon */}
          <section className="rounded-2xl border border-zinc-200 bg-white p-6">
            <div className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold">Discount Code</h2>
            </div>
            <div className="mt-4 flex gap-2">
              <input
                placeholder="Enter coupon code (try WELCOME10)"
                value={couponCode}
                onChange={(e) => {
                  setCouponCode(e.target.value);
                  setCouponApplied(false);
                }}
                className="flex-1 rounded-lg border border-zinc-200 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
              <button
                onClick={applyCoupon}
                className="rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-zinc-800"
              >
                Apply
              </button>
            </div>
            {couponError && <p className="mt-2 text-sm text-red-500">{couponError}</p>}
            {couponApplied && (
              <p className="mt-2 text-sm text-green-600">
                Coupon applied! You save {formatCurrency(discount)}
              </p>
            )}
          </section>

          {/* Payment */}
          <section className="rounded-2xl border border-zinc-200 bg-white p-6">
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold">Payment</h2>
            </div>
            <p className="mt-4 rounded-lg bg-indigo-50 p-4 text-sm text-indigo-800">
              Simulated payment gateway. Click &ldquo;Place Order&rdquo; to complete your purchase
              instantly.
            </p>
          </section>
        </div>

        {/* Summary */}
        <div className="h-fit rounded-2xl border border-zinc-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Order Summary</h2>
          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <div key={item.productId} className="flex justify-between text-sm">
                <span className="text-zinc-600">
                  {item.name} x{item.quantity}
                </span>
                <span>{formatCurrency(item.price * item.quantity)}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-2 border-t border-zinc-200 pt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-zinc-600">Subtotal</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-600">Shipping</span>
              <span>{shippingCost === 0 ? "Free" : formatCurrency(shippingCost)}</span>
            </div>
            {discount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>-{formatCurrency(discount)}</span>
              </div>
            )}
          </div>
          <div className="mt-4 flex justify-between border-t border-zinc-200 pt-4">
            <span className="font-semibold">Total</span>
            <span className="text-xl font-bold">{formatCurrency(total)}</span>
          </div>
          <button
            onClick={placeOrder}
            disabled={processing}
            className="mt-6 w-full rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {processing ? "Processing..." : "Place Order"}
          </button>
        </div>
      </div>
    </div>
  );
}
