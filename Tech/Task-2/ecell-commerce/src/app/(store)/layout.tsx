/**
 * Store Layout — shared chrome for all customer-facing pages.
 *
 * The (store) folder is a Route Group — parentheses mean it does NOT
 * appear in the URL. This layout adds Navbar + Footer around pages like
 * /, /shop, /cart, /checkout, etc.
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
