/**
 * Store Layout — shared chrome for customer-facing pages.
 *
 * ROLE IN THE APP:
 *   The (store) folder is a Route Group — parentheses exclude it from the URL.
 *   Adds Navbar + Footer around /, /shop, /cart, /checkout, /orders, /login, etc.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Route groups organize files without affecting URL structure
 *   - Admin routes (/admin/*) use a separate layout with sidebar (no Navbar/Footer)
 *   - main.flex-1 grows to push Footer to bottom (sticky footer layout)
 */
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </>
  );
}
