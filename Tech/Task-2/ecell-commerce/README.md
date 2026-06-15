# E-Cell Store

Full-stack e-commerce platform for **E-Cell Tech Domain Task 2** — storefront, checkout, order tracking, and admin dashboard.

| | |
|---|---|
| **Live demo** | https://ecell-commerce.vercel.app |
| **Repository** | https://github.com/KanakMalpani/ecell-commerce |

## Features

**Customer app:** landing page, product catalog with search/filters, cart, checkout (coupons + simulated payment), order history and tracking.

**Admin panel (`/admin`):** analytics, product CRUD, order management, coupon and banner management.

**Backend:** JWT auth (HTTP-only cookies), role-based access (Admin/User), REST APIs, SQLite + Prisma.

## Tech stack

Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 · Prisma 7 · SQLite · bcrypt · JWT

## Quick start

**Requirements:** Node.js 18+, npm

```bash
git clone https://github.com/KanakMalpani/ecell-commerce.git
cd ecell-commerce
cp .env.example .env
npm install
npm run db:setup:local
npm run dev
```

Open http://localhost:3000

### Environment variables

Copy `.env.example` to `.env` and set:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLite path (default `file:./dev.db`) |
| `JWT_SECRET` | **Required in production.** Use a long random string (32+ chars). Never commit real secrets. |

## Demo access (evaluation only)

These accounts are seeded for reviewers. **Change or remove them before any real deployment.**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@ecell.com | admin123 |
| User | user@ecell.com | user123 |

Sample coupon codes: `WELCOME10`, `FLAT200`, `ECCELL25`

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm start` | Run production server |
| `npm run db:setup:local` | Migrate + seed (local first run) |
| `npm run db:setup` | Migrate deploy + seed (CI/production) |

## Project structure

```
src/app/(store)/   Customer pages (shop, cart, checkout, orders)
src/app/admin/     Admin dashboard
src/app/api/       REST API routes
src/components/    UI components
src/context/       Auth and cart state
src/lib/           Auth, Prisma, utilities
prisma/            Schema, migrations, seed data
```

## API overview

| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/api/auth` | Public (register) |
| PUT | `/api/auth` | Public (login) |
| DELETE | `/api/auth` | Authenticated |
| GET | `/api/products` | Public |
| POST | `/api/orders` | Authenticated |
| GET | `/api/analytics` | Admin |
| GET | `/api/coupons` | Admin |

## Security

- Passwords hashed with bcrypt; JWT stored in HTTP-only cookies
- Admin routes and mutating APIs enforce role checks server-side
- `.env` and database files are gitignored; only `.env.example` is tracked
- Production **requires** `JWT_SECRET` — the app fails to start without it
- Demo credentials are for evaluation; rotate secrets and passwords for production use
- Do not commit `.env`, `dev.db`, or Vercel/local config files

## Deployment

**Vercel (current):** https://ecell-commerce.vercel.app

1. Import the GitHub repo in Vercel
2. Set `JWT_SECRET` and `DATABASE_URL` in project environment variables
3. Build command (already in `vercel.json`): `npx prisma migrate deploy && npx tsx prisma/seed.ts && npm run build`

**Render:** `render.yaml` is included for SQLite-friendly hosting with persistent disk.

## AI prompts

See [AI_PROMPTS.md](./AI_PROMPTS.md) for prompts used during development.

## License

Built for E-Cell Tech Domain evaluation.
