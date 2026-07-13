/**
 * CartContext — shopping cart persisted in localStorage.
 *
 * ROLE IN THE APP:
 *   Manages cart items entirely on the client so guests can shop before login.
 *   Syncs to localStorage on every change. Checkout reads this state and sends
 *   productId + quantity to POST /api/orders (server validates stock/prices).
 *
 * KEY PATTERN:
 *   Cart is NOT stored server-side — intentional for demo simplicity.
 *   Stock caps enforced client-side (UX) and server-side (security).
 *
 * PI INTERVIEW TALKING POINTS:
 *   - localStorage vs cookie: cart doesn't need server access; larger payload OK
 *   - addItem merges quantities for same productId; respects stock ceiling
 *   - Server re-fetches product prices at checkout to prevent price tampering
 */
"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";

export type CartItem = {
  productId: string;
  name: string;
  price: number;
  imageUrl: string;
  slug: string;
  quantity: number;
  stock: number;
};

type CartContextType = {
  items: CartItem[];
  addItem: (item: Omit<CartItem, "quantity">, quantity?: number) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  totalItems: number;
  subtotal: number;
};

const CartContext = createContext<CartContextType | null>(null);
const CART_KEY = "ecell_cart"; // localStorage key for cart persistence

/** CartProvider — restores cart from localStorage and exposes cart mutations. */
export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  // Restore cart from localStorage on first mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(CART_KEY);
      if (stored) setItems(JSON.parse(stored));
    } catch {
      /* ignore */
    }
    setLoaded(true);
  }, []);

  // Save cart to localStorage whenever items change (after initial load)
  useEffect(() => {
    if (loaded) {
      localStorage.setItem(CART_KEY, JSON.stringify(items));
    }
  }, [items, loaded]);

  // Merge into existing line item or add new; never exceed available stock
  const addItem = useCallback(
    (item: Omit<CartItem, "quantity">, quantity = 1) => {
      setItems((prev) => {
        const existing = prev.find((i) => i.productId === item.productId);
        if (existing) {
          const newQty = Math.min(existing.quantity + quantity, item.stock);
          return prev.map((i) =>
            i.productId === item.productId ? { ...i, quantity: newQty, stock: item.stock } : i
          );
        }
        return [...prev, { ...item, quantity: Math.min(quantity, item.stock) }];
      });
    },
    []
  );

  const removeItem = useCallback((productId: string) => {
    setItems((prev) => prev.filter((i) => i.productId !== productId));
  }, []);

  const updateQuantity = useCallback((productId: string, quantity: number) => {
    setItems((prev) =>
      prev
        .map((i) =>
          i.productId === productId
            ? { ...i, quantity: Math.max(0, Math.min(quantity, i.stock)) }
            : i
        )
        .filter((i) => i.quantity > 0)
    );
  }, []);

  const clearCart = useCallback(() => setItems([]), []);

  const totalItems = items.reduce((sum, i) => sum + i.quantity, 0);
  const subtotal = items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  return (
    <CartContext.Provider
      value={{ items, addItem, removeItem, updateQuantity, clearCart, totalItems, subtotal }}
    >
      {children}
    </CartContext.Provider>
  );
}

/** Hook to access cart state — must be used inside <CartProvider>. */
export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
