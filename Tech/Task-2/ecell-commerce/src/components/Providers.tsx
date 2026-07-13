/**
 * Providers — root-level React Context wrapper.
 *
 * ROLE IN THE APP:
 *   Next.js Server Components can't use Context, so this thin client component
 *   is imported in layout.tsx to wrap the entire app tree.
 *
 * PROVIDER ORDER: AuthProvider → CartProvider
 *   Auth must be outer so checkout can check login status before cart operations.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Composition pattern: one Providers file keeps layout.tsx as Server Component
 *   - Provider nesting order matters when contexts depend on each other
 */
"use client";

import { ReactNode } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { CartProvider } from "@/context/CartContext";

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <CartProvider>{children}</CartProvider>
    </AuthProvider>
  );
}
