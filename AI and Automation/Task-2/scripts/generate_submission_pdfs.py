#!/usr/bin/env python
"""
=============================================================================
Submission PDF Generator — Presentation Deck & System Report
=============================================================================

PURPOSE
-------
Produces deliverable PDF artifacts for project submission and PI interviews:
  - Task-2-Presentation.pdf  — slide-deck overview of architecture & results
  - SYSTEM_REPORT.pdf        — rendered copy of SYSTEM_REPORT.md

ROLE IN THE RAG PIPELINE
------------------------
  Post-pipeline utility (runs AFTER Stage 4 evaluation). Reads evaluation
  outputs from reports/ and packages them for human consumption — does not
  affect RAG inference or indexing.

  Dependency chain:
    run_evaluate.py → metrics_comparison.csv
    SYSTEM_REPORT.md (authored separately)
    generate_submission_pdfs.py → submission/*.pdf

INTERVIEW TALKING POINTS
------------------------
1. **Evaluation → visualization loop:** metrics_comparison.csv is the single
   source of truth for the results table in the presentation slide.
2. **ReportLab Platypus:** Uses flowables (Paragraph, Table, Spacer) for
   professional PDF layout vs. low-level canvas in create_sample_pdf.py.
3. **Three pipeline comparison slide:** Demonstrates you benchmarked local_llm,
   reranked_local, and extractive — not just one happy path.
4. **Anti-hallucination slide:** Explicitly calls out guardrails — shows
   production-minded design beyond "chatbot over PDFs."
5. **Markdown → PDF:** Simple line-prefix parser for SYSTEM_REPORT.md; trade-off
   is no full CommonMark support but zero extra dependencies.

USAGE:
    python scripts/run_evaluate.py && python scripts/generate_submission_pdfs.py

REQUIRES:
    pip install reportlab
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SUBMISSION_DIR = ROOT / "submission"
METRICS_CSV = ROOT / "reports" / "metrics_comparison.csv"
SYSTEM_REPORT_MD = ROOT / "SYSTEM_REPORT.md"


# ---------------------------------------------------------------------------
# Data loading — read evaluation CSV produced by Stage 4
# ---------------------------------------------------------------------------
def load_metrics() -> list[dict[str, str]]:
    """
    Load pipeline comparison rows from reports/metrics_comparison.csv.

    Returns empty list if evaluation hasn't been run yet (graceful degradation
    in presentation — slides still generate, just without results table).
    """
    if not METRICS_CSV.exists():
        return []
    with METRICS_CSV.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return [{k: ("" if v is None else str(v)) for k, v in row.items()} for row in rows]


# ---------------------------------------------------------------------------
# Slide builder — reusable canvas for bullet-point slides
# ---------------------------------------------------------------------------
def slide_canvas(title: str, bullets: list[str], subtitle: str = "") -> list:
    """
    Build a single presentation slide as a list of ReportLab flowables.

    Interview note: landscape letter + large title font mimics standard
    conference slide proportions for submission review.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SlideTitle",
        parent=styles["Heading1"],
        fontSize=28,
        spaceAfter=16,
        textColor=colors.HexColor("#1a365d"),
    )
    body_style = ParagraphStyle(
        "SlideBody",
        parent=styles["BodyText"],
        fontSize=14,
        leading=20,
        spaceAfter=8,
    )
    story: list = [Paragraph(title, title_style)]
    if subtitle:
        story.append(Paragraph(subtitle, body_style))
        story.append(Spacer(1, 0.15 * inch))
    for bullet in bullets:
        story.append(Paragraph(f"&bull; {bullet}", body_style))
    story.append(PageBreak())
    return story


# ---------------------------------------------------------------------------
# Presentation PDF — multi-slide deck with optional metrics table
# ---------------------------------------------------------------------------
def build_presentation_pdf(output: Path, metrics: list[dict[str, str]]) -> None:
    """
    Assemble the full Task-2 presentation deck.

    Slides cover: problem statement, five-stage pipeline, three pipeline paths,
    evaluation results (if available), anti-hallucination, live demo, deliverables.
    """
    doc = SimpleDocTemplate(
        str(output),
        pagesize=landscape(letter),
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    story: list = []

    story += slide_canvas(
        "E-Cell AI &amp; Automation - Task 2",
        [
            "Enterprise Knowledge Management &amp; Semantic Retrieval (RAG)",
            "Fully local inference with Ollama + ChromaDB",
            "GitHub: KanakMalpani/Ecell-Projects",
        ],
        subtitle="Knowledge Management &amp; Semantic Retrieval System",
    )

    story += slide_canvas(
        "Problem Statement",
        [
            "Organizational docs hold critical operational knowledge",
            "Manual search is slow, error-prone, and inefficient",
            "Goal: ingest PDFs/text, index embeddings, run grounded Q&amp;A via API",
        ],
    )

    story += slide_canvas(
        "Five-Stage Pipeline",
        [
            "Stage 1: Document ingestion &amp; text segmentation (pdfplumber, chunking)",
            "Stage 2: Embedding generation &amp; ChromaDB indexing (MiniLM-L6-v2)",
            "Stage 3: LLM inference &amp; context orchestration (Ollama + reranker)",
            "Stage 4: Pipeline evaluation (CR, F, AR, L, QR)",
            "Stage 5: FastAPI deployment (POST /query with source metadata)",
        ],
    )

    story += slide_canvas(
        "Three Pipeline Paths (Ollama)",
        [
            "local_llm - vector search + Ollama (qwen2.5:7b)",
            "reranked_local - cross-encoder rerank + Ollama [RECOMMENDED]",
            "extractive - retrieval-only baseline (no LLM)",
        ],
    )

    # Evaluation results table — only if metrics CSV exists from Stage 4
    if metrics:
        styles = getSampleStyleSheet()
        story.append(Paragraph("Evaluation Results", styles["Heading1"]))
        story.append(Spacer(1, 0.2 * inch))
        table_data = [["Pipeline", "CR", "F", "AR", "QR", "L (ms)"]]
        for row in metrics:
            pipeline = row.get("") or next(iter(row.values()), "")
            table_data.append([
                pipeline,
                row.get("CR", ""),
                row.get("F", ""),
                row.get("AR", ""),
                row.get("QR", ""),
                row.get("L_ms", ""),
            ])
        table = Table(table_data, colWidths=[1.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ])
        )
        story.append(table)
        story.append(PageBreak())

    story += slide_canvas(
        "Anti-Hallucination Guardrails",
        [
            "Context-only system prompt; mandatory source citations",
            "Similarity threshold (0.25) before LLM invocation",
            "Abstention phrase when context is insufficient",
            "Confidence derived from vector similarity scores",
            "Source metadata returned with every API response",
        ],
    )

    story += slide_canvas(
        "Live Demo",
        [
            "POST /query via FastAPI Swagger (127.0.0.1:8001/docs)",
            "Show sources[].similarity and source_file in responses",
            "Dynamic ingestion: backup_recovery_sop.pdf (7 docs, 43 chunks)",
            "Example: VPN lockout procedure, password policy, GDPR breach timeline",
        ],
    )

    story += slide_canvas(
        "Deliverables &amp; Submission",
        [
            "Source code: AI and Automation/Task-2/ on GitHub",
            "System report: SYSTEM_REPORT.md + SYSTEM_REPORT.pdf",
            "Evaluation: reports/metrics_comparison.csv + .png",
            "This presentation: submission/Task-2-Presentation.pdf",
        ],
    )

    doc.build(story)
    print(f"Created {output}")


# ---------------------------------------------------------------------------
# System report PDF — lightweight Markdown → PDF renderer
# ---------------------------------------------------------------------------
def build_system_report_pdf(output: Path) -> None:
    """
    Convert SYSTEM_REPORT.md to a formatted PDF.

    Uses prefix-based line classification (# heading, ## subheading, | table,
    - bullet). Not a full Markdown parser — sufficient for the project's
    authored report structure.
    """
    text = SYSTEM_REPORT_MD.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=8)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=14)

    story: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.08 * inch))
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(stripped[2:], h1))
        elif stripped.startswith("## "):
            story.append(Paragraph(stripped[3:], h2))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 0.1 * inch))
        elif stripped.startswith("|"):
            safe = stripped.replace("&", "&amp;")
            story.append(Paragraph(f"<font face='Courier' size='8'>{safe}</font>", body))
        elif stripped.startswith("- "):
            story.append(Paragraph(f"&bull; {stripped[2:]}", body))
        elif stripped.startswith("*") and stripped.endswith("*"):
            story.append(Paragraph(f"<i>{stripped.strip('*')}</i>", body))
        else:
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body))

    doc.build(story)
    print(f"Created {output}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Generate both submission PDFs into submission/ directory."""
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    metrics = load_metrics()
    build_presentation_pdf(SUBMISSION_DIR / "Task-2-Presentation.pdf", metrics)
    build_system_report_pdf(SUBMISSION_DIR / "SYSTEM_REPORT.pdf")


if __name__ == "__main__":
    main()
