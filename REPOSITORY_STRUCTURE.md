# E-Cell Repository Structure

```
E-Cell/
├── README.md
│
├── AI and Automation/
│   ├── Task-1/                              # 10-K SEC filing risk classification
│   │   ├── api/app.py
│   │   ├── create_submission_video.py
│   │   ├── data/processed_filings.csv
│   │   ├── notebooks/eda.ipynb
│   │   ├── reports/
│   │   ├── run_pipeline.py
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── evaluate.py
│   │       ├── features.py
│   │       ├── preprocess.py
│   │       ├── text_preprocessor.py
│   │       ├── train.py
│   │       └── utils.py
│   │
│   ├── Task-2/                              # Enterprise RAG knowledge retrieval
│   │   ├── api/app.py
│   │   ├── config/settings.yaml
│   │   ├── data/
│   │   │   ├── eval_questions.json
│   │   │   ├── processed/chunks.json
│   │   │   └── raw/                         # SOPs, policies, regulations (PDF/TXT)
│   │   ├── models/state/
│   │   ├── reports/
│   │   ├── run_pipeline.py
│   │   ├── scripts/
│   │   │   ├── create_sample_pdf.py
│   │   │   ├── generate_submission_pdfs.py
│   │   │   ├── run_embed.py
│   │   │   ├── run_evaluate.py
│   │   │   └── run_ingest.py
│   │   ├── src/
│   │   │   ├── embed.py
│   │   │   ├── evaluate.py
│   │   │   ├── ingest.py
│   │   │   ├── orchestrate.py
│   │   │   ├── text_preprocessor.py
│   │   │   └── utils.py
│   │   └── submission/
│   │
│   └── Task-3/                              # AI-integrated CRM platform
│       ├── api/app.py
│       ├── dashboard/index.html
│       ├── data/synthetic_crm_dataset.json
│       ├── models/prompts.yaml
│       ├── notebooks/exploratory_llm.ipynb
│       ├── reports/
│       ├── run_pipeline.py
│       ├── scripts/
│       │   ├── generate_charts.py
│       │   ├── generate_data.py
│       │   ├── generate_submission_pdfs.py
│       │   ├── run_ingest.py
│       │   └── verify_all.py
│       ├── src/
│       │   ├── __init__.py
│       │   ├── agents.py
│       │   ├── auth.py
│       │   ├── cohort.py
│       │   ├── config.py
│       │   ├── crm.py
│       │   ├── database.py
│       │   ├── heart.py
│       │   ├── llm.py
│       │   ├── memory.py
│       │   └── security.py
│       ├── start_demo.ps1
│       └── submission/
│
└── Tech/
    ├── Task-1/                              # GNN Logistics landing page (React + Vite)
    │   └── client/
    │       ├── index.html
    │       ├── src/
    │       │   ├── App.jsx
    │       │   ├── main.jsx
    │       │   ├── index.css
    │       │   ├── components/
    │       │   │   ├── About.jsx
    │       │   │   ├── Contact.jsx
    │       │   │   ├── Footer.jsx
    │       │   │   ├── Hero.jsx
    │       │   │   ├── Navbar.jsx
    │       │   │   ├── Services.jsx
    │       │   │   └── Testimonials.jsx
    │       │   └── data/site.js
    │       ├── eslint.config.js
    │       └── vite.config.js
    │
    └── Task-2/                              # E-Cell commerce app (Next.js + Prisma)
        └── ecell-commerce/
            ├── next.config.ts
            ├── prisma/
            │   ├── schema.prisma
            │   ├── seed.ts
            │   └── migrations/
            ├── prisma.config.ts
            ├── render.yaml
            └── src/
                ├── app/
                │   ├── globals.css
                │   ├── layout.tsx
                │   ├── (store)/             # Customer-facing pages
                │   │   ├── page.tsx
                │   │   ├── cart/page.tsx
                │   │   ├── checkout/page.tsx
                │   │   ├── login/page.tsx
                │   │   ├── register/page.tsx
                │   │   ├── orders/
                │   │   └── shop/
                │   ├── admin/               # Admin dashboard pages
                │   │   ├── page.tsx
                │   │   ├── banners/page.tsx
                │   │   ├── coupons/page.tsx
                │   │   ├── orders/page.tsx
                │   │   └── products/page.tsx
                │   └── api/                 # REST API routes
                │       ├── analytics/route.ts
                │       ├── addresses/route.ts
                │       ├── auth/
                │       ├── banners/
                │       ├── categories/route.ts
                │       ├── coupons/
                │       ├── orders/
                │       └── products/
                ├── components/
                │   ├── Providers.tsx
                │   ├── layout/
                │   └── shop/
                ├── context/
                │   ├── AuthContext.tsx
                │   └── CartContext.tsx
                ├── lib/
                │   ├── auth.ts
                │   ├── prisma.ts
                │   └── utils.ts
                └── types/index.ts
```
