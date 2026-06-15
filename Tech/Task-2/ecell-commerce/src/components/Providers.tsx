/**
 * Providers — wraps the app with all React Context providers.
 *
 * Next.js Server Components cannot use Context, so we create this small
 * client component and import it in the root layout. AuthProvider must
 * wrap CartProvider so checkout can check login status.
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
