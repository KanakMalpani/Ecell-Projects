# E-Cell Tech - Web Development Induction

Complete implementation of the **Web Development Learning Roadmap** from `Tech Resources ( Ecell Inductions ).pdf`.

This folder demonstrates progression from static HTML/CSS/JavaScript pages to a full **MERN** application themed with E-Cell colors (`#FFB800`, `#000000`, `#FFFFFF`).

## Roadmap coverage

| Module | Folder / Feature | What was built |
|--------|------------------|----------------|
| 1. HTML | `modules/01-html/` | Semantic page with nav, table, and form |
| 2. CSS | `modules/02-css/` | Flexbox cards, CSS Grid calendar, club theme |
| 3. JavaScript | `modules/03-javascript/` | DOM filters, RSVP counter, localStorage |
| 4. React | `client/` | SPA with routing and reusable components |
| 5. Node & Express | `server/` | REST API for events, applications, resources |
| 6. MongoDB | `server/src/models/` | Mongoose schemas and persistence |
| 7. MERN Stack | `client/` + `server/` | Integrated frontend, backend, and database |
| 8. Git & GitHub | repository root | Version control with `Tech/` and `AI and Automation/` split |

## Project structure

```
Tech/
├── modules/          # Static HTML, CSS, JS demos (Modules 1-3)
├── client/           # React frontend (Modules 4 & 7)
├── server/           # Express + MongoDB API (Modules 5-7)
└── Tech Resources ( Ecell Inductions ).pdf
```

## Prerequisites

- Node.js 18+
- MongoDB running locally (or MongoDB Atlas URI)

## Quick start

### 1. Backend

```bash
cd server
cp .env.example .env
npm install
npm run seed
npm run dev
```

API: http://localhost:5000/api/health

### 2. Frontend

```bash
cd client
cp .env.example .env
npm install
npm run dev
```

App: http://localhost:5173

## App features

- **Home** - roadmap overview and induction summary
- **Modules** - links to static HTML/CSS/JS demos
- **Events** - view and create club events (API + MongoDB)
- **Resources** - learning links from the induction PDF
- **Join** - domain application form saved to MongoDB

## Notes

- Static demos are also copied to `client/public/modules/` for easy access during development.
- If MongoDB is not running, the API starts but database routes will fail until connected.
