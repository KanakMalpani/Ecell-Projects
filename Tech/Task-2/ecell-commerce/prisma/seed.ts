import "dotenv/config";
import { PrismaClient } from "../src/generated/prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import bcrypt from "bcryptjs";

const url = process.env.DATABASE_URL ?? "file:./dev.db";
const adapter = new PrismaBetterSqlite3({ url });
const prisma = new PrismaClient({ adapter });

async function main() {
  await prisma.orderItem.deleteMany();
  await prisma.order.deleteMany();
  await prisma.address.deleteMany();
  await prisma.product.deleteMany();
  await prisma.category.deleteMany();
  await prisma.coupon.deleteMany();
  await prisma.banner.deleteMany();
  await prisma.user.deleteMany();

  const adminPassword = await bcrypt.hash("admin123", 10);
  const userPassword = await bcrypt.hash("user123", 10);

  await prisma.user.create({
    data: {
      email: "admin@ecell.com",
      password: adminPassword,
      name: "E-Cell Admin",
      role: "ADMIN",
    },
  });

  const user = await prisma.user.create({
    data: {
      email: "user@ecell.com",
      password: userPassword,
      name: "Demo User",
      role: "USER",
    },
  });

  await prisma.address.create({
    data: {
      userId: user.id,
      label: "Home",
      street: "123 Innovation Drive",
      city: "Hyderabad",
      state: "Telangana",
      zipCode: "500032",
      isDefault: true,
    },
  });

  const categories = await Promise.all(
    [
      { name: "Electronics", slug: "electronics" },
      { name: "Fashion", slug: "fashion" },
      { name: "Home & Living", slug: "home-living" },
      { name: "Accessories", slug: "accessories" },
    ].map((c) => prisma.category.create({ data: c }))
  );

  const products = [
    {
      name: "Wireless Noise-Cancelling Headphones",
      slug: "wireless-headphones",
      description:
        "Premium over-ear headphones with 40-hour battery life, active noise cancellation, and studio-quality sound for work and travel.",
      price: 4999,
      stock: 45,
      imageUrl:
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
      featured: true,
      categoryId: categories[0].id,
    },
    {
      name: "Smart Fitness Watch Pro",
      slug: "smart-fitness-watch",
      description:
        "Track heart rate, sleep, and workouts with a vibrant AMOLED display and 7-day battery life.",
      price: 3499,
      stock: 60,
      imageUrl:
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
      featured: true,
      categoryId: categories[0].id,
    },
    {
      name: "Minimalist Leather Backpack",
      slug: "leather-backpack",
      description:
        "Handcrafted full-grain leather backpack with laptop compartment and water-resistant lining.",
      price: 2799,
      stock: 30,
      imageUrl:
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
      featured: true,
      categoryId: categories[3].id,
    },
    {
      name: "Organic Cotton Hoodie",
      slug: "organic-cotton-hoodie",
      description:
        "Ultra-soft organic cotton hoodie with relaxed fit. Perfect for campus life and casual outings.",
      price: 1899,
      stock: 80,
      imageUrl:
        "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&q=80",
      featured: false,
      categoryId: categories[1].id,
    },
    {
      name: "Desk Lamp with Wireless Charging",
      slug: "desk-lamp-charger",
      description:
        "Modern LED desk lamp with adjustable brightness, color temperature, and built-in Qi wireless charger.",
      price: 2299,
      stock: 25,
      imageUrl:
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80",
      featured: false,
      categoryId: categories[2].id,
    },
    {
      name: "Portable Bluetooth Speaker",
      slug: "bluetooth-speaker",
      description:
        "360-degree sound, IPX7 waterproof, and 12-hour playtime. Ideal for events and outdoor sessions.",
      price: 1599,
      stock: 55,
      imageUrl:
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80",
      featured: true,
      categoryId: categories[0].id,
    },
    {
      name: "Ceramic Pour-Over Coffee Set",
      slug: "coffee-pour-over-set",
      description:
        "Artisan ceramic dripper with glass carafe. Elevate your morning ritual with barista-quality brews.",
      price: 1299,
      stock: 40,
      imageUrl:
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80",
      featured: false,
      categoryId: categories[2].id,
    },
    {
      name: "Classic Aviator Sunglasses",
      slug: "aviator-sunglasses",
      description:
        "Polarized lenses with UV400 protection. Timeless style meets all-day comfort.",
      price: 999,
      stock: 100,
      imageUrl:
        "https://images.unsplash.com/photo-1572635196233-14a0e43d1f41?w=800&q=80",
      featured: false,
      categoryId: categories[3].id,
    },
  ];

  await prisma.product.createMany({ data: products });

  await prisma.coupon.createMany({
    data: [
      {
        code: "WELCOME10",
        type: "PERCENTAGE",
        value: 10,
        minOrder: 500,
        expiresAt: new Date("2027-12-31"),
        maxUses: 1000,
      },
      {
        code: "FLAT200",
        type: "FIXED",
        value: 200,
        minOrder: 1500,
        expiresAt: new Date("2027-06-30"),
        maxUses: 500,
      },
      {
        code: "ECCELL25",
        type: "PERCENTAGE",
        value: 25,
        minOrder: 2000,
        expiresAt: new Date("2026-12-31"),
        maxUses: 100,
      },
    ],
  });

  await prisma.banner.createMany({
    data: [
      {
        title: "Summer Tech Sale",
        subtitle: "Up to 40% off on electronics. Limited time only.",
        imageUrl:
          "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80",
        link: "/shop?category=electronics",
        active: true,
        sortOrder: 1,
      },
      {
        title: "New Arrivals",
        subtitle: "Discover the latest in fashion and lifestyle.",
        imageUrl:
          "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&q=80",
        link: "/shop",
        active: true,
        sortOrder: 2,
      },
      {
        title: "Free Shipping",
        subtitle: "On all orders above ₹999. Shop now.",
        imageUrl:
          "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1200&q=80",
        link: "/shop",
        active: true,
        sortOrder: 3,
      },
    ],
  });

  console.log("Seed completed.");
  console.log("Admin: admin@ecell.com / admin123");
  console.log("User: user@ecell.com / user123");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
