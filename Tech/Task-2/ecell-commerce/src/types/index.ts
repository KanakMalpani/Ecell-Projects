/**
 * Shared TypeScript Types — frontend data contracts.
 *
 * ROLE IN THE APP:
 *   Defines the shape of JSON returned by API routes for type-safe UI code.
 *   These are simplified views of Prisma models — they omit sensitive fields
 *   (e.g. password) and flatten nested relations for component props.
 *
 * USAGE: import type { Product, Order } from "@/types"
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Separating API response types from Prisma types decouples UI from DB schema
 *   - `type` imports are erased at compile time (zero runtime cost)
 *   - Optional fields (category?, _count?) reflect Prisma `include` variations
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
