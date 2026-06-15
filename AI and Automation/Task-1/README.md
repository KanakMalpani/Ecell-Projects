# E-Cell AI & Automation - Task 1

10-K SEC filing classification project for the document intelligence assignment.

## Problem

Classify financial filings into **low / medium / high risk** using text from SEC 10-K reports.

Dataset: [winterForestStump/10-K_sec_filings](https://huggingface.co/datasets/winterForestStump/10-K_sec_filings)

Labels are created from the **Risk Factors** section using keyword-based scoring and tertile bucketing. Details are in `MODEL_REPORT.md`.

## Folder structure

```
data/          # processed data saved here after running pipeline
notebooks/     # basic EDA
src/           # pipeline code (preprocess, features, train, evaluate)
api/           # FastAPI app
models/        # saved model files after training
reports/       # metrics and confusion matrices after evaluation
```

## Setup

```bash
pip install -r requirements.txt
```

## Run pipeline

```bash
python run_pipeline.py --max-samples 800
```

This loads filings, preprocesses text, builds TF-IDF features, trains XGBoost / AdaBoost / CatBoost, and saves the best model.

## Run API

Train the model first, then:

```bash
uvicorn api.app:app --reload
```

Docs: http://127.0.0.1:8000/docs

Example:

```json
POST /predict
{"text": "The company faces litigation, covenant breaches, and going concern uncertainty."}
```

Response:

```json
{"label": "high", "confidence": 0.85}
```
