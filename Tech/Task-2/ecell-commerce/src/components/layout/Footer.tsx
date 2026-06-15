import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-zinc-200 bg-zinc-50">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
                EC
              </span>
              <span className="text-lg font-semibold text-zinc-900">E-Cell Store</span>
            </div>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-zinc-600">
              Your campus marketplace for premium products. Built by E-Cell Tech Domain
              for seamless shopping experiences.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-zinc-900">Shop</h3>
            <ul className="mt-4 space-y-2 text-sm text-zinc-600">
              <li><Link href="/shop" className="hover:text-indigo-600">All Products</Link></li>
              <li><Link href="/shop?category=electronics" className="hover:text-indigo-600">Electronics</Link></li>
              <li><Link href="/shop?category=fashion" className="hover:text-indigo-600">Fashion</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-zinc-900">Support</h3>
            <ul className="mt-4 space-y-2 text-sm text-zinc-600">
              <li><Link href="/orders" className="hover:text-indigo-600">Track Orders</Link></li>
              <li><Link href="/login" className="hover:text-indigo-600">Account</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-10 border-t border-zinc-200 pt-6 text-center text-sm text-zinc-500">
          &copy; {new Date().getFullYear()} E-Cell Tech Domain. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
