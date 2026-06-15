import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Shield, Truck, RefreshCw, Star } from "lucide-react";
import ProductCard from "@/components/shop/ProductCard";
import { prisma } from "@/lib/prisma";
import { isBannerActive } from "@/lib/utils";

const testimonials = [
  {
    name: "Priya Sharma",
    role: "Computer Science Student",
    text: "Amazing selection and fast delivery. The checkout was smooth and I got my order within days!",
    rating: 5,
  },
  {
    name: "Arjun Reddy",
    role: "Entrepreneurship Club",
    text: "E-Cell Store has become our go-to for event merchandise. Quality products at great prices.",
    rating: 5,
  },
  {
    name: "Sneha Patel",
    role: "Design Lead",
    text: "Love the clean interface and product quality. The coupon codes saved me a lot on my last order.",
    rating: 5,
  },
];

export default async function HomePage() {
  const [products, allBanners] = await Promise.all([
    prisma.product.findMany({
      where: { featured: true },
      include: { category: true },
      take: 4,
    }),
    prisma.banner.findMany({ orderBy: { sortOrder: "asc" } }),
  ]);

  const banners = allBanners.filter(isBannerActive);
  const heroBanner = banners[0];

  return (
    <div>
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-indigo-900 to-violet-900 text-white">
        <div className="absolute inset-0 opacity-20">
          {heroBanner && (
            <Image src={heroBanner.imageUrl} alt="" fill className="object-cover" priority />
          )}
        </div>
        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="max-w-2xl">
            <span className="inline-block rounded-full bg-white/10 px-4 py-1 text-sm font-medium backdrop-blur">
              E-Cell Tech Domain
            </span>
            <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Shop smarter.
              <br />
              <span className="text-indigo-300">Live better.</span>
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-indigo-100">
              Discover curated products from electronics to fashion. Premium quality,
              campus-friendly prices, and a checkout experience built for you.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href="/shop"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-indigo-900 transition hover:bg-indigo-50"
              >
                Shop Now
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/shop?category=electronics"
                className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Browse Electronics
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-zinc-200 bg-white">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-4 py-10 sm:grid-cols-4 sm:px-6 lg:px-8">
          {[
            { icon: Truck, label: "Free shipping over ₹999" },
            { icon: Shield, label: "Secure checkout" },
            { icon: RefreshCw, label: "Easy returns" },
            { icon: Star, label: "4.9/5 customer rating" },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Icon className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-zinc-700">{label}</span>
            </div>
          ))}
        </div>
      </section>

      {banners.length > 1 && (
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-zinc-900">Promotions</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {banners.slice(1).map((banner) => (
              <Link
                key={banner.id}
                href={banner.link || "/shop"}
                className="group relative overflow-hidden rounded-2xl"
              >
                <div className="relative aspect-[2/1]">
                  <Image
                    src={banner.imageUrl}
                    alt={banner.title}
                    fill
                    className="object-cover transition duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                  <div className="absolute bottom-0 p-6 text-white">
                    <h3 className="text-xl font-bold">{banner.title}</h3>
                    {banner.subtitle && (
                      <p className="mt-1 text-sm text-white/80">{banner.subtitle}</p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="bg-zinc-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-900">Featured Products</h2>
              <p className="mt-2 text-zinc-600">Hand-picked favorites from our catalog</p>
            </div>
            <Link href="/shop" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
              View all →
            </Link>
          </div>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-2xl font-bold text-zinc-900">
            Loved by our community
          </h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {testimonials.map((t) => (
              <div
                key={t.name}
                className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
              >
                <div className="flex gap-1">
                  {Array.from({ length: t.rating }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="mt-4 text-sm leading-relaxed text-zinc-600">&ldquo;{t.text}&rdquo;</p>
                <div className="mt-4">
                  <p className="font-semibold text-zinc-900">{t.name}</p>
                  <p className="text-xs text-zinc-500">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-indigo-600 py-16 text-white">
        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold">Ready to start shopping?</h2>
          <p className="mx-auto mt-4 max-w-xl text-indigo-100">
            Join thousands of happy customers. Use code WELCOME10 for 10% off your first order.
          </p>
          <Link
            href="/shop"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3 text-sm font-semibold text-indigo-900 transition hover:bg-indigo-50"
          >
            Explore the Store
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
