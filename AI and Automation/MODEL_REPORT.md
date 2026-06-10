# Model Report - Task 1

## Classification target

I defined a **financial risk classification** task with 3 classes: `low`, `medium`, `high`.

The dataset does not come with labels, so I used the **Risk Factors** section from each 10-K filing. This section is where companies describe major business risks, so it fits the task well.

**How labels were created:**
1. Count high-risk keywords (e.g. bankruptcy, litigation, going concern) and medium-risk keywords (e.g. uncertain, regulatory, volatile) in the Risk Factors text.
2. Convert this into a risk score using keyword density.
3. Split filings into 3 equal groups using score ranks: lowest third = low, middle = medium, highest = high.

Dataset used: Hugging Face `winterForestStump/10-K_sec_filings`, split `026`. I loaded 800 filings and kept 283 after removing very short / empty records.

---

## Preprocessing

- Downloaded parquet file from Hugging Face Hub
- Lowercased text and removed HTML tags, extra symbols, and repeated whitespace
- Removed common boilerplate like "table of contents", SEC header text, page numbers
- Extracted 4 sections when available:
  - Risk Factors
  - Business Overview
  - MD&A
  - Financial Statements
- Combined these sections into one document for modeling
- Dropped filings with less than 30 words after cleaning

---

## Features

Main feature set: **TF-IDF** (required)

Settings:
- max 5000 features
- unigrams and bigrams
- min document frequency = 2

Extra custom features added:
- total document word count
- word count for each section
- ratio of risk section length to full document length

I did not use the label risk score directly as a feature to avoid leakage.

---

## Model comparison

Train/test split: 80/20 (stratified)

| Model | Accuracy | Precision | Recall | F1 |
|-------|----------|-----------|--------|-----|
| XGBoost | 0.737 | 0.781 | 0.737 | 0.711 |
| CatBoost | 0.719 | 0.751 | 0.719 | 0.683 |
| AdaBoost | 0.632 | 0.474 | 0.632 | 0.526 |

Confusion matrices are saved in `reports/` after running the pipeline.

### Observations

- **XGBoost** performed best overall.
- **High risk** class was detected well (precision 1.00 for XGBoost).
- **Medium risk** was the hardest class (lower recall), likely because the language overlaps with both low and high risk filings.
- **AdaBoost** struggled most and barely predicted the low class correctly.

---

## Best model

**Selected model: XGBoost**

Reason: highest accuracy and macro F1 among the three models, and more balanced results across classes compared to AdaBoost. CatBoost was close but slightly worse on medium-risk recall.

Saved as `models/best_model.joblib` after running `run_pipeline.py`.

---

## API

FastAPI endpoint in `api/app.py`:
- `POST /predict` with input `{ "text": "..." }`
- Output `{ "label": "...", "confidence": 0.xx }`
- Swagger UI at `/docs`
