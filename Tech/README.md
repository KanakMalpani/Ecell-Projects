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
| Google Sheets automation | Ready | `google-apps-script/Code.gs` + `VITE_GOOGLE_SCRIPT_URL` |
| Social media links | Done | `client/src/components/Footer.jsx` |
| Footer with company info | Done | `client/src/components/Footer.jsx` |
| Loading / motion animations | Done | Framer Motion |
| Hover effects | Done | Service cards + buttons |

## Tech stack

- React (Vite)
- Tailwind CSS
- Framer Motion
- Google Apps Script (form -> Sheets)

## Project structure

```
Tech/
├── client/                  # Landing page app
├── google-apps-script/      # Sheets automation script
├── E-cell Tech Domain Task-1.pdf
├── Tech Resources ( Ecell Inductions ).pdf
├── AI_PROMPTS.md
└── README.md
```

## Setup

```bash
cd client
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173

### Production build

```bash
cd client
npm run build
npm run preview
```

## Google Sheets automation

1. Create a Google Sheet with columns: `Timestamp, Name, Email, Phone, Service, Message`
2. Open **Extensions -> Apps Script**
3. Paste `google-apps-script/Code.gs` and set `SPREADSHEET_ID`
4. Deploy as **Web app** (execute as you, access: anyone)
5. Put the deployment URL in `client/.env`:

```env
VITE_GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

## Deployment

Deploy the `client/dist` folder to any static host:

- [Vercel](https://vercel.com)
- [Netlify](https://netlify.com)
- [GitHub Pages](https://pages.github.com) (with `base` config if needed)

**Live site:** https://client-sigma-virid.vercel.app

### Vercel environment variable (required for form -> Sheets)

After deploying the Apps Script web app, add this in the Vercel dashboard  
(Project **client** -> Settings -> Environment Variables):

```
GOOGLE_SCRIPT_URL = https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

Or from terminal:

```bash
cd client
npx vercel env add GOOGLE_SCRIPT_URL production
npx vercel deploy --prod
```

## AI prompts

See [AI_PROMPTS.md](AI_PROMPTS.md) for the prompts used during development.

## Note on earlier work

An earlier version in this repo built a MERN club demo. That did **not** match Task 1. The landing page in `client/` is the corrected submission. The old `server/` folder is deprecated.
