"""
Stage 4: Pipeline evaluation with RAG metrics.

Runs a set of test questions (data/eval_questions.json) through each
pipeline mode and scores them on five metrics:

  CR  — Context Relevance:  did we retrieve the right document chunks?
  F   — Faithfulness:       is the answer grounded in the retrieved text?
  AR  — Answer Relevance:    does the answer actually address the question?
  L   — Latency (ms):        how fast was the response?
  QR  — Query Resolution:   did the answer contain expected keywords?

Outputs:
  reports/evaluation_report.json
  reports/metrics_comparison.csv
  reports/metrics_comparison.png
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


@dataclass
class EvalMetrics:
    """Scores for one question on one pipeline."""
    context_relevance: float
    faithfulness: float
    answer_relevance: float
    latency_ms: float
    query_resolved: bool


def _contains_any(text: str, keywords: list[str]) -> bool:
    """Check if the answer contains any of the expected keywords (for QR score)."""
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


def _source_excerpt(source: Any) -> str:
    """Extract excerpt text from a SourceMetadata object or dict."""
    return getattr(source, "excerpt", "") or (source.get("excerpt", "") if isinstance(source, dict) else "")


def score_context_relevance(query: str, sources: list[Any], embedder: SentenceTransformer) -> float:
    """
    CR: How relevant are the retrieved chunks to the question?

    Computes cosine similarity between query embedding and each source excerpt.
    Returns the maximum similarity (best matching chunk).
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
    F: Is the answer grounded in the retrieved sources (not hallucinated)?

    Splits the answer into sentences and checks each against source excerpts.
    High score = answer sentences closely match retrieved text.
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
    AR: Does the answer actually address the question asked?

    Cosine similarity between query and answer embeddings.
    Low score if the model abstained or gave an off-topic answer.
    """
    if "cannot find sufficient information" in answer.lower():
        return 0.2
    q_emb = embedder.encode([query], normalize_embeddings=True)
    a_emb = embedder.encode([answer], normalize_embeddings=True)
    return float(cosine_similarity(q_emb, a_emb)[0][0])


def evaluate_single(
    pipeline: RAGPipeline,
    question: dict[str, Any],
    embedder: SentenceTransformer,
) -> dict[str, Any]:
    """Run one eval question through the pipeline and compute all metrics."""
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


def aggregate_results(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Average all per-question metrics into pipeline-level summary scores."""
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
    """Draw a bar chart comparing CR, F, AR, QR across pipeline modes."""
    df = pd.DataFrame(summary).T[["CR", "F", "AR", "QR"]]
    ax = df.plot(kind="bar", figsize=(10, 6), rot=0)
    ax.set_title("RAG Pipeline Evaluation Metrics")
    ax.set_ylabel("Score (0-1)")
    ax.set_ylim(0, 1.05)
    ax.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def run_evaluation(pipelines: list[str] | None = None) -> dict[str, Any]:
    """
    Full evaluation: run all questions through each pipeline, pick the best.

    Winner = highest QR (query resolution), then faithfulness, then lowest latency.
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


def main() -> None:
    """CLI entry point: python scripts/run_evaluate.py"""
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
