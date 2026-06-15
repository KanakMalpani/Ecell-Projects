"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Tag,
  Image as ImageIcon,
  ArrowLeft,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const navItems = [
  { href: "/admin", label: "Analytics", icon: LayoutDashboard },
  { href: "/admin/products", label: "Products", icon: Package },
  { href: "/admin/orders", label: "Orders", icon: ShoppingCart },
  { href: "/admin/coupons", label: "Coupons", icon: Tag },
  { href: "/admin/banners", label: "Banners", icon: ImageIcon },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && (!user || user.role !== "ADMIN")) {
      router.push("/login?redirect=/admin");
    }
  }, [user, loading, router]);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
  }

  if (!user || user.role !== "ADMIN") return null;

  return (
    <div className="flex min-h-screen bg-zinc-50">
      <aside className="fixed inset-y-0 left-0 z-40 w-64 border-r border-zinc-200 bg-white">
        <div className="flex h-16 items-center gap-2 border-b border-zinc-200 px-6">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">
            EC
          </span>
          <span className="font-semibold text-zinc-900">Admin Panel</span>
        </div>
        <nav className="p-4 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                pathname === href
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-zinc-200 p-4">
          <Link
            href="/"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-600 hover:bg-zinc-50"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Store
          </Link>
          <button
            onClick={() => logout()}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </aside>
      <main className="ml-64 flex-1 p-8">{children}</main>
    </div>
  );
}
