#!/usr/bin/env python
"""
Generate HEART and cohort charts for reports and submission deck.

WHAT THIS FILE DOES
-------------------
Creates two PNG charts in reports/ from live CRM data:
  1. heart_metrics.png    — bar chart of all 5 HEART dimensions (0-100 scale)
  2. retention_curve.png  — line chart of largest cohort's 6-month retention

USED BY
-------
  scripts/generate_submission_pdfs.py embeds these charts in submission PDFs.
  Also useful for manual inspection before evaluation.

RUN
---
  python scripts/generate_charts.py
  (auto-run by generate_submission_pdfs.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from src.cohort import cohort_engine
from src.heart import heart_service

REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def chart_heart() -> Path:
    scores = heart_service.compute_all()
    labels = ["Happiness\n(CSAT/5)", "Engagement\n(score)", "Adoption\n(%)", "Retention\n(%)", "Task Success\n(%)"]
    values = [
        scores["happiness"]["avg_csat"] / 5 * 100,
        scores["engagement"]["avg_engagement_score"],
        scores["adoption"]["feature_adoption_proxy"] * 100,
        scores["retention"]["monthly_retention"] * 100,
        scores["task_success"]["resolution_rate"] * 100,
    ]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color=["#3b82f6", "#6366f1", "#8b5cf6", "#a855f7", "#d946ef"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Score (0-100 scale)")
    ax.set_title("HEART Framework Metrics (Live CRM Data)")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{val:.1f}", ha="center", fontsize=9)
    fig.tight_layout()
    out = REPORTS / "heart_metrics.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Created {out}")
    return out


def chart_retention() -> Path:
    cid = cohort_engine.largest_cohort() or "default"
    curve = cohort_engine.retention_curve(cid, periods=6)
    periods = [p["period"] for p in curve]
    rates = [p["retention_rate"] * 100 for p in curve]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(periods, rates, marker="o", linewidth=2, color="#3b82f6")
    ax.set_xlabel("Month offset")
    ax.set_ylabel("Retention rate (%)")
    ax.set_title(f"Cohort Retention Curve — {cid[:40]}")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = REPORTS / "retention_curve.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Created {out}")
    return out


def main() -> None:
    chart_heart()
    chart_retention()


if __name__ == "__main__":
    main()
