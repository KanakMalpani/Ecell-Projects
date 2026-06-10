# E-Cell Tech Domain - Task 1

**GNN Logistics Inc. Company Landing Page**

Task brief: [`E-cell Tech Domain Task-1.pdf`](E-cell%20Tech%20Domain%20Task-1.pdf)

Learning resources (separate reference): [`Tech Resources ( Ecell Inductions ).pdf`](Tech%20Resources%20(%20Ecell%20Inductions%20).pdf)

## Objective

Develop a modern, responsive landing page for **GNN Logistics Inc.** that showcases brand, services, testimonials, and a contact inquiry flow.

## Task checklist

| Requirement | Status | Location |
|-------------|--------|----------|
| Responsive design (desktop/tablet/mobile) | Done | Tailwind responsive grids + mobile nav |
| Hero section with CTA | Done | `client/src/components/Hero.jsx` |
| Company overview & mission | Done | `client/src/components/About.jsx` |
| Services showcase | Done | `client/src/components/Services.jsx` |
| Testimonials | Done | `client/src/components/Testimonials.jsx` |
| Contact / inquiry form | Done | `client/src/components/Contact.jsx` |
| Form validation | Done | `Contact.jsx` |
| Social media links | Done | `client/src/components/Footer.jsx` |
| Footer with company info | Done | `client/src/components/Footer.jsx` |
| Loading / motion animations | Done | Framer Motion |
| Hover effects | Done | Service cards + buttons |

## Tech stack

- React (Vite)
- Tailwind CSS
- Framer Motion

## Project structure

```
Tech/
├── client/                  # Landing page app
├── E-cell Tech Domain Task-1.pdf
├── Tech Resources ( Ecell Inductions ).pdf
├── AI_PROMPTS.md
└── README.md
```

## Setup

```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173

### Production build

```bash
cd client
npm run build
npm run preview
```

## Contact form

The form validates input client-side, then opens the user's email app with a pre-filled message to `contact@gnnlogistics.com`. No backend or Google Sheets setup is required.

## Deployment

**Live site:** https://client-sigma-virid.vercel.app

```bash
cd client
npx vercel deploy --prod
```

## AI prompts

See [AI_PROMPTS.md](AI_PROMPTS.md) for the prompts used during development.
