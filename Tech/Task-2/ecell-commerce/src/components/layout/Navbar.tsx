"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShoppingCart, User, Menu, X, LayoutDashboard } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useCart } from "@/context/CartContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { totalItems } = useCart();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAdmin = pathname.startsWith("/admin");

  const links = [
    { href: "/", label: "Home" },
    { href: "/shop", label: "Shop" },
    { href: "/orders", label: "Orders" },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200/80 bg-white/90 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
            EC
          </span>
          <span className="text-lg font-semibold tracking-tight text-zinc-900">
            E-Cell Store
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {!isAdmin &&
            links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors hover:text-indigo-600 ${
                  pathname === link.href ? "text-indigo-600" : "text-zinc-600"
                }`}
              >
                {link.label}
              </Link>
            ))}
          {user?.role === "ADMIN" && (
            <Link
              href="/admin"
              className="flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              <LayoutDashboard className="h-4 w-4" />
              Admin
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3">
          {!isAdmin && (
            <Link
              href="/cart"
              className="relative rounded-full p-2 text-zinc-600 transition hover:bg-zinc-100 hover:text-indigo-600"
            >
              <ShoppingCart className="h-5 w-5" />
              {totalItems > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                  {totalItems}
                </span>
              )}
            </Link>
          )}

          {user ? (
            <div className="hidden items-center gap-3 md:flex">
              <span className="text-sm text-zinc-600">{user.name}</span>
              <button
                onClick={() => logout()}
                className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="hidden items-center gap-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 md:flex"
            >
              <User className="h-4 w-4" />
              Login
            </Link>
          )}

          <button
            className="rounded-lg p-2 text-zinc-600 md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {mobileOpen && (
        <div className="border-t border-zinc-100 bg-white px-4 py-4 md:hidden">
          {!isAdmin &&
            links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block py-2 text-sm font-medium text-zinc-700"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          {user?.role === "ADMIN" && (
            <Link
              href="/admin"
              className="block py-2 text-sm font-medium text-indigo-600"
              onClick={() => setMobileOpen(false)}
            >
              Admin Dashboard
            </Link>
          )}
          {user ? (
            <button
              onClick={() => {
                logout();
                setMobileOpen(false);
              }}
              className="mt-2 block w-full rounded-lg border border-zinc-200 py-2 text-sm font-medium"
            >
              Logout ({user.name})
            </button>
          ) : (
            <Link
              href="/login"
              className="mt-2 block rounded-lg bg-indigo-600 py-2 text-center text-sm font-medium text-white"
              onClick={() => setMobileOpen(false)}
            >
              Login
            </Link>
          )}
        </div>
      )}
    </header>
  );
}
