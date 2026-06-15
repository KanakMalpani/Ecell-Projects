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

export type Category = {
  id: string;
  name: string;
  slug: string;
  _count?: { products: number };
};

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

export type Banner = {
  id: string;
  title: string;
  subtitle: string | null;
  imageUrl: string;
  link: string | null;
};

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
