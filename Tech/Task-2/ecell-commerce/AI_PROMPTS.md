# AI Prompts Used for E-Cell Store Development

This document records the AI prompts used to build this e-commerce platform.

## Initial Task Prompt

```
Complete the tasks in Tech task.pdf - Develop a modern E-Commerce Platform with:
- Customer-facing landing page with hero, featured products, testimonials
- Storefront with product listing, detail pages, search/filter, cart
- Checkout with address, coupons, simulated payment, order tracking
- Admin dashboard with product/order/analytics/coupon/banner management
- Backend with auth, RBAC, database integration
- Tech stack: Node.js, Express (via Next.js API routes), React/Next.js, Tailwind CSS
```

## Architecture Prompt

```
Build a Next.js full-stack app with:
- Prisma + SQLite for easy local setup
- JWT auth with HTTP-only cookies and role-based access (ADMIN/USER)
- Client-side cart with localStorage persistence
- Server components for landing page data fetching via Prisma
- Admin panel with sidebar navigation
```

## UI/Design Prompt

```
Create a modern, high-conversion e-commerce design with:
- Indigo/violet brand colors for E-Cell branding
- Responsive grid layouts for product cards
- Trust indicators (free shipping, secure checkout, ratings)
- Clean admin dashboard with stat cards and data tables
- Framer Motion ready structure (using CSS transitions for simplicity)
```

## Feature-Specific Prompts

### Checkout Flow
```
Implement checkout with shipping address form, saved addresses for logged-in users,
coupon validation API, order summary, simulated payment gateway, and order confirmation page.
```

### Admin Analytics
```
Build analytics dashboard showing total revenue, order count, conversion rate,
top-selling products, order status breakdown, recent 30-day revenue, and low stock alerts.
```

### Order Tracking
```
Add visual order tracking timeline showing CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED
status progression on the order detail page.
```

## Seed Data Prompt

```
Seed the database with:
- Admin user (admin@ecell.com) and demo user (user@ecell.com)
- 4 categories: Electronics, Fashion, Home & Living, Accessories
- 8 products with Unsplash images and realistic Indian pricing in INR
- 3 coupon codes: WELCOME10, FLAT200, ECCELL25
- 3 promotional banners for homepage
```

## Documentation Prompt

```
Write README with setup instructions, demo accounts, API overview, deployment guide for Vercel,
and project structure. Include this AI_PROMPTS.md file as a deliverable.
```
