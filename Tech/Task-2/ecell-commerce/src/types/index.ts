/**
 * Shared TypeScript types for the E-Cell Store frontend.
 *
 * These types describe the shape of data returned by API routes.
 * They mirror the Prisma database models but are simplified for the UI.
 * Import them with: import type { Product } from "@/types"
 */

// ─── Product & Category ───────────────────────────────────────────────────────

/** A product in the store catalog. */
export type Product = {
  id: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  stock: number;
  imageUrl: string;
  featured: boolean;
  categoryId: string;
  category?: { id: string; name: string; slug: string };
};

/** A product category (e.g. Electronics, Fashion). */
export type Category = {
  id: string;
  name: string;
  slug: string;
  _count?: { products: number };
};

// ─── Orders ───────────────────────────────────────────────────────────────────

/** A customer order with line items and shipping details. */
export type Order = {
  id: string;
  orderNumber: string;
  status: string;
  paymentStatus: string;
  subtotal: number;
  discount: number;
  total: number;
  couponCode: string | null;
  shippingStreet: string;
  shippingCity: string;
  shippingState: string;
  shippingZip: string;
  shippingCountry: string;
  createdAt: string;
  items: {
    id: string;
    quantity: number;
    price: number;
    product: Product;
  }[];
  user?: { name: string; email: string };
};

// ─── Marketing ────────────────────────────────────────────────────────────────

/** A homepage promotional banner image with optional link. */
export type Banner = {
  id: string;
  title: string;
  subtitle: string | null;
  imageUrl: string;
  link: string | null;
};

/** A discount coupon — either percentage off or a fixed rupee amount. */
export type Coupon = {
  id: string;
  code: string;
  type: "PERCENTAGE" | "FIXED";
  value: number;
  minOrder: number;
  expiresAt: string;
  active: boolean;
  maxUses: number | null;
  usedCount: number;
};

// ─── Admin ────────────────────────────────────────────────────────────────────

/** Dashboard metrics shown on the admin analytics page. */
export type Analytics = {
  totalRevenue: number;
  recentRevenue: number;
  totalOrders: number;
  paidOrders: number;
  conversionRate: number;
  topProducts: { name: string; quantity: number; revenue: number }[];
  statusBreakdown: Record<string, number>;
  lowStock: { id: string; name: string; stock: number }[];
  totalProducts: number;
  totalCustomers: number;
};

/** A saved shipping address for a logged-in user. */
export type Address = {
  id: string;
  label: string;
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  isDefault: boolean;
};
