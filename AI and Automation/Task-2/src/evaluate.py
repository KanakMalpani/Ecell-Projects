"""
=============================================================================
Stage 4: RAG Pipeline Evaluation & Selection
=============================================================================

PURPOSE
-------
Systematically benchmarks multiple RAG pipeline configurations against a gold
question set and recommends the best mode for production deployment.

ROLE IN THE RAG PIPELINE
------------------------
  Input:  data/eval_questions.json (queries + expected_answer_contains keywords)
          ChromaDB index + Ollama (for generative modes)
  Output: reports/evaluation_report.json
          reports/metrics_comparison.csv
          reports/metrics_comparison.png
          recommended_pipeline → consumed by run_pipeline.py → pipeline_state.json

  This stage closes the loop: build → measure → deploy the winner.

METRICS (INTERVIEW CHEAT SHEET)
-------------------------------
  CR  — Context Relevance:  cosine(query, retrieved excerpts) — retrieval quality
  F   — Faithfulness:       answer sentences grounded in source excerpts
  AR  — Answer Relevance:   cosine(query, answer) — on-topic response
  L   — Latency (ms):       wall-clock per query (retrieval + LLM)
  QR  — Query Resolution:   binary — answer contains expected keywords

  Winner: max(QR) → max(F) → min(L) — task success first, then grounding, then speed.

INTERVIEW TALKING POINTS
------------------------
1. **Three pipeline modes:** extractive (no LLM baseline), local_llm (vector+LLM),
   reranked_local (cross-encoder precision + LLM) — shows deliberate architecture choices.
2. **Embedding-based CR/F/AR:** Reuses same MiniLM model as retrieval — no extra API
   cost; trade-off is metrics correlate with retrieval model, not human judgment.
3. **Faithfulness via sentence grounding:** Splits answer into sentences, checks each
   against source excerpts — catches hallucinated clauses even when answer sounds right.
4. **QR keyword check:** Simple but effective for enterprise eval sets where answers
   must mention specific policy numbers, procedures, or compliance terms.
5. **Automated recommendation:** Output drives api/app.py ACTIVE_MODE — eval is not
   just a report, it controls deployment configuration.
"""

from __future__ import annotations

import argparse
import re
import time
from dataclasses import asdict, dataclass
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.orchestrate import RAGPipeline
from src.utils import load_config, load_json, resolve_path, save_json, setup_logging

logger = setup_logging("evaluate")


# -----------------------------------------------------------------------------
# Data model — per-question metric bundle
# -----------------------------------------------------------------------------
@dataclass
class EvalMetrics:
    """Aggregated scores for one (question, pipeline) pair."""
    context_relevance: float
    faithfulness: float
    answer_relevance: float
    latency_ms: float
    query_resolved: bool


# -----------------------------------------------------------------------------
# Scoring helpers — keyword check and excerpt extraction
# -----------------------------------------------------------------------------
def _contains_any(text: str, keywords: list[str]) -> bool:
    """
    Query Resolution (QR): check if answer contains any expected keyword.

    Case-insensitive substring match — simple but effective for policy-number
    and procedure-name validation in enterprise eval sets.
    """
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


def _source_excerpt(source: Any) -> str:
    """Normalize SourceMetadata object or dict to excerpt text for metric computation."""
    return getattr(source, "excerpt", "") or (source.get("excerpt", "") if isinstance(source, dict) else "")


# -----------------------------------------------------------------------------
# Metric functions — CR, F, AR
# -----------------------------------------------------------------------------
def score_context_relevance(query: str, sources: list[Any], embedder: SentenceTransformer) -> float:
    """
    CR — Context Relevance: how well do retrieved chunks match the question?

    Embeds query and each source excerpt; returns MAX cosine similarity.
    Interview: max (not mean) rewards finding at least one highly relevant chunk.
    """
    if not sources:
        return 0.0
    query_emb = embedder.encode([query], normalize_embeddings=True)
    ctx_texts = [_source_excerpt(s) for s in sources]
    ctx_emb = embedder.encode(ctx_texts, normalize_embeddings=True)
    sims = cosine_similarity(query_emb, ctx_emb)[0]
    return float(max(sims))


def score_faithfulness(answer: str, sources: list[Any], embedder: SentenceTransformer) -> float:
    """
    F — Faithfulness: is the answer grounded in retrieved sources?

    Splits answer into sentences (>20 chars), embeds each, checks max similarity
    to any source excerpt. Mean of per-sentence maxes = overall faithfulness.

    Special cases:
      - Abstention phrase with no sources → 1.0 (correct behavior)
      - Abstention with sources present → 0.8 (conservative abstention)
      - No sources but non-abstention answer → 0.0 (likely hallucination)
    """
    abstain = "cannot find sufficient information"
    if abstain in answer.lower():
        return 1.0 if not sources else 0.8
    if not sources:
        return 0.0

    sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 20]
    if not sentences:
        return 0.5

    ctx_texts = [_source_excerpt(s) for s in sources]
    ctx_emb = embedder.encode(ctx_texts, normalize_embeddings=True)
    sent_emb = embedder.encode(sentences, normalize_embeddings=True)
    sim_matrix = cosine_similarity(sent_emb, ctx_emb)
    return float(sim_matrix.max(axis=1).mean())


def score_answer_relevance(query: str, answer: str, embedder: SentenceTransformer) -> float:
    """
    AR — Answer Relevance: does the answer address the question?

    Cosine similarity between query and answer embeddings.
    Abstention answers score 0.2 (technically on-topic but unhelpful).
    """
    if "cannot find sufficient information" in answer.lower():
        return 0.2
    q_emb = embedder.encode([query], normalize_embeddings=True)
    a_emb = embedder.encode([answer], normalize_embeddings=True)
    return float(cosine_similarity(q_emb, a_emb)[0][0])


# -----------------------------------------------------------------------------
# Per-question evaluation — run pipeline + compute all metrics
# -----------------------------------------------------------------------------
def evaluate_single(
    pipeline: RAGPipeline,
    question: dict[str, Any],
    embedder: SentenceTransformer,
) -> dict[str, Any]:
    """
    Run one eval question through the pipeline and compute CR, F, AR, L, QR.

    Returns a detail row stored in evaluation_report.json for post-hoc analysis.
    """
    result = pipeline.query(question["query"])
    cr = score_context_relevance(question["query"], result.sources, embedder)
    f = score_faithfulness(result.answer, result.sources, embedder)
    ar = score_answer_relevance(question["query"], result.answer, embedder)
    resolved = _contains_any(result.answer, question["expected_answer_contains"])

    metrics = EvalMetrics(
        context_relevance=round(cr, 4),
        faithfulness=round(f, 4),
        answer_relevance=round(ar, 4),
        latency_ms=result.latency_ms,
        query_resolved=resolved,
    )

    return {
        "question_id": question["id"],
        "query": question["query"],
        "pipeline": pipeline.mode,
        "answer": result.answer,
        "confidence": result.confidence,
        "metrics": asdict(metrics),
        "retrieval_scores": result.retrieval_scores,
        "sources": [asdict(s) for s in result.sources],
    }


# -----------------------------------------------------------------------------
# Aggregation & visualization
# -----------------------------------------------------------------------------
def aggregate_results(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Average per-question metrics into pipeline-level summary (CR, F, AR, L, QR)."""
    if not rows:
        return {}
    df = pd.DataFrame([r["metrics"] for r in rows])
    return {
        "CR": round(df["context_relevance"].mean(), 4),
        "F": round(df["faithfulness"].mean(), 4),
        "AR": round(df["answer_relevance"].mean(), 4),
        "L_ms": round(df["latency_ms"].mean(), 1),
        "QR": round(df["query_resolved"].mean(), 4),
    }


def plot_comparison(summary: dict[str, dict[str, float]], output_path: str) -> None:
    """
    Bar chart comparing CR, F, AR, QR across pipeline modes.

    Saved to reports/metrics_comparison.png for submission deck inclusion.
    Latency (L) omitted from chart — different scale (ms vs 0-1 scores).
    """
    df = pd.DataFrame(summary).T[["CR", "F", "AR", "QR"]]
    ax = df.plot(kind="bar", figsize=(10, 6), rot=0)
    ax.set_title("RAG Pipeline Evaluation Metrics")
    ax.set_ylabel("Score (0-1)")
    ax.set_ylim(0, 1.05)
    ax.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


# -----------------------------------------------------------------------------
# run_evaluation — full Stage 4 orchestration
# -----------------------------------------------------------------------------
def run_evaluation(pipelines: list[str] | None = None) -> dict[str, Any]:
    """
    Full evaluation: run all questions through each pipeline, pick the best.

    Winner selection key: (QR desc, F desc, L_ms asc) — task success prioritized.

    Returns:
        Full report dict with summary, per-pipeline details, recommended_pipeline,
        and recommendation_reason string for logging/submission.
    """
    config = load_config()
    questions = load_json(resolve_path(config["evaluation"]["eval_questions_file"]))
    modes = pipelines or ["local_llm", "reranked_local", "extractive"]
    embedder = SentenceTransformer(config["embedding"]["model_name"])

    all_results: dict[str, Any] = {"pipelines": {}, "details": {}}
    summary: dict[str, dict[str, float]] = {}

    for mode in modes:
        logger.info("Evaluating pipeline: %s", mode)
        pipeline = RAGPipeline(mode=mode)  # type: ignore[arg-type]
        rows: list[dict[str, Any]] = []
        for question in questions:
            rows.append(evaluate_single(pipeline, question, embedder))
        agg = aggregate_results(rows)
        summary[mode] = agg
        all_results["details"][mode] = rows
        logger.info("%s -> CR=%.3f F=%.3f AR=%.3f QR=%.3f L=%.0fms", mode, agg["CR"], agg["F"], agg["AR"], agg["QR"], agg["L_ms"])

    all_results["summary"] = summary
    best = max(summary.items(), key=lambda item: (item[1]["QR"], item[1]["F"], -item[1]["L_ms"]))
    all_results["recommended_pipeline"] = best[0]
    all_results["recommendation_reason"] = (
        f"Highest QR ({best[1]['QR']}) with strong faithfulness ({best[1]['F']}) "
        f"and acceptable latency ({best[1]['L_ms']} ms)."
    )

    reports_dir = resolve_path(config["paths"]["reports_dir"])
    save_json(reports_dir / "evaluation_report.json", all_results)
    pd.DataFrame(summary).T.to_csv(reports_dir / "metrics_comparison.csv")
    plot_comparison(summary, str(reports_dir / "metrics_comparison.png"))

    logger.info("Recommended pipeline: %s", best[0])
    return all_results


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: python scripts/run_evaluate.py [--pipelines ...]"""
    parser = argparse.ArgumentParser(description="Stage 4: evaluate RAG pipelines")
    parser.add_argument(
        "--pipelines",
        nargs="+",
        default=None,
        help="Pipeline modes to evaluate (default: all three)",
    )
    args = parser.parse_args()
    run_evaluation(pipelines=args.pipelines)


if __name__ == "__main__":
    main()
