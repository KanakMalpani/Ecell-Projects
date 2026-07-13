#!/usr/bin/env python
"""
Generate submission PDFs for Task 3: presentation deck and system report.

WHAT THIS FILE DOES
-------------------
Builds two submission artifacts in submission/:
  1. Task-3-Presentation.pdf  — slide deck with live metrics + charts
  2. SYSTEM_REPORT.pdf        — converts SYSTEM_REPORT.md to PDF with appendix

PIPELINE
--------
  1. Run generate_charts.py for fresh PNG charts
  2. Load live metrics from heart_service + cohort_engine
  3. Build presentation slides (ReportLab SimpleDocTemplate, landscape)
  4. Parse SYSTEM_REPORT.md → PDF with tables, code blocks, chart appendix

RUN BEFORE SUBMISSION
---------------------
  python scripts/generate_submission_pdfs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SUBMISSION_DIR = ROOT / "submission"
SYSTEM_REPORT_MD = ROOT / "SYSTEM_REPORT.md"
HEART_CHART = ROOT / "reports" / "heart_metrics.png"
RETENTION_CHART = ROOT / "reports" / "retention_curve.png"


def _clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier' size='9'>\1</font>", text)
    text = text.replace("→", "-&gt;").replace("—", "-")
    return text


def _load_live_metrics() -> dict:
    from src.cohort import cohort_engine
    from src.heart import heart_service

    heart = heart_service.compute_all()
    churn = cohort_engine.train_churn_model()
    cid = cohort_engine.largest_cohort() or "all"
    curve = cohort_engine.retention_curve(cid) if cid != "all" else []
    m6 = curve[-1]["retention_rate"] if curve else heart["retention"]["monthly_retention"]
    return {
        "heart": heart,
        "churn": churn,
        "cohort_id": cid,
        "month6_retention": m6,
    }


def slide_canvas(title: str, bullets: list[str], subtitle: str = "") -> list:
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
        story.append(Paragraph(f"&bull; {_clean_inline(bullet)}", body_style))
    story.append(PageBreak())
    return story


def metrics_table_slide(metrics: dict) -> list:
    styles = getSampleStyleSheet()
    h = metrics["heart"]
    c = metrics["churn"]
    story: list = [
        Paragraph("Evaluation Results (Live CRM Data)", styles["Heading1"]),
        Spacer(1, 0.2 * inch),
    ]
    table_data = [
        ["Metric", "Value"],
        ["Avg CSAT (Happiness)", f"{h['happiness']['avg_csat']:.2f} / 5"],
        ["Active customers (Engagement)", str(h["engagement"]["active_customers"])],
        ["AI-assisted ticket rate (Adoption)", f"{h['adoption']['ai_assisted_ticket_rate'] * 100:.1f}%"],
        ["Monthly retention (Retention)", f"{h['retention']['monthly_retention'] * 100:.1f}%"],
        ["Ticket resolution rate (Task Success)", f"{h['task_success']['resolution_rate'] * 100:.1f}%"],
        ["Churn model F1", f"{c.get('f1', 0):.2f}"],
        ["Churn-flagged customers", str(c.get("flagged_customers", "N/A"))],
        ["Largest cohort M+6 retention", f"{metrics['month6_retention'] * 100:.1f}%"],
    ]
    table = Table(table_data, colWidths=[3.2 * inch, 2.5 * inch])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.Color(0.95, 0.95, 0.95)]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(table)
    story.append(PageBreak())
    return story


def chart_slide(title: str, chart_path: Path) -> list:
    styles = getSampleStyleSheet()
    story: list = [
        Paragraph(title, styles["Heading1"]),
        Spacer(1, 0.2 * inch),
        Image(str(chart_path), width=7 * inch, height=3.85 * inch),
        PageBreak(),
    ]
    return story


def build_presentation_pdf(output: Path, metrics: dict) -> None:
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
        "E-Cell AI &amp; Automation - Task 3",
        [
            "AI-Integrated CRM Platform for E-Cell Operations",
            "Local LLM inference via Ollama (Llama-3-8B-Instruct)",
            "GitHub: KanakMalpani/Ecell-Projects",
        ],
        subtitle="Customer Intelligence, Agents, Cohort Analysis &amp; HEART Metrics",
    )

    story += slide_canvas(
        "Problem Statement",
        [
            "Startups lack AI-native CRM tools for tickets, interactions, and workflows",
            "Build enterprise-grade CRM with LLM summarization and agent automation",
            "Measure impact via HEART framework and cohort retention analytics",
        ],
    )

    story += slide_canvas(
        "Five-Module Architecture",
        [
            "Module 1: Customer &amp; ticket CRUD, segmentation, timeline views",
            "Module 2: LangChain summarization + LangGraph agent workflows + memory",
            "Module 3: Cohort retention curves, churn scoring, JSON/PDF export",
            "Module 4: HEART dashboard (Happiness, Engagement, Adoption, Retention, Task Success)",
            "Module 5: FastAPI backend with RBAC and audit metadata",
        ],
    )

    story += slide_canvas(
        "Synthetic Dataset",
        [
            "520 customer profiles across 6 industries and 3 product tiers",
            "1,050+ support tickets with full lifecycle states",
            "2,500+ interaction logs spanning ~6 months",
            "Bulk ingestion with validation and deduplication on startup",
        ],
    )

    story += slide_canvas(
        "LLM Stack (Ollama Local)",
        [
            "Ticket summarization: key issues, urgency, resolution path",
            "LangGraph pipeline: load context -&gt; route -&gt; generate -&gt; escalation",
            "Hallucination guard: source citations, confidence scoring, flag unsourced claims",
            "Per-customer short-term + long-term interaction memory",
        ],
    )

    story += slide_canvas(
        "Role-Based Access Control",
        [
            "Agent: create/query tickets, run summarization and agent pipeline",
            "Supervisor: agent permissions + cohort analysis read access",
            "Admin: full system access across all CRM modules",
            "Analytics: read-only HEART metrics, cohorts, and customer data",
        ],
    )

    story += slide_canvas(
        "Core API Endpoints",
        [
            "POST /api/v1/customers - create customer with cohort assignment",
            "POST /api/v1/tickets/create - ticket lifecycle management",
            "POST /api/v1/tickets/{id}/summarize - LangChain summarization",
            "POST /api/v1/query/agent - LangGraph multi-turn agent",
            "GET /api/v1/cohorts/analysis - retention curves and churn scores",
        ],
    )

    story += slide_canvas(
        "HEART Framework Metrics",
        [
            "Happiness: CSAT and NPS proxy by cohort/channel",
            "Engagement: active customers, ticket open rates, session depth",
            "Adoption: AI-assisted ticket rate, onboarding completion",
            "Retention: monthly retention, churn flags, lifespan by segment",
            "Task Success: resolution rate, FCR, escalation frequency",
        ],
    )

    story += metrics_table_slide(metrics)

    if HEART_CHART.exists():
        story += chart_slide("HEART Metrics Chart", HEART_CHART)
    if RETENTION_CHART.exists():
        story += chart_slide(f"Retention Curve - {metrics['cohort_id'][:45]}", RETENTION_CHART)

    story += slide_canvas(
        "Live Demo",
        [
            "Swagger UI: http://127.0.0.1:8002/docs",
            "HEART dashboard: http://127.0.0.1:8002/dashboard",
            "Agent query with memory-aware multi-turn context",
            "Cohort report export to JSON and PDF",
        ],
    )

    story += slide_canvas(
        "Deliverables",
        [
            "Source code: AI and Automation/Task-3/ on GitHub",
            "System report: SYSTEM_REPORT.md + submission/SYSTEM_REPORT.pdf",
            "Presentation: submission/Task-3-Presentation.pdf",
            "Run: python run_pipeline.py then uvicorn api.app:app --port 8002",
        ],
    )

    doc.build(story)
    print(f"Created {output}")


def _parse_table_rows(lines: list[str]) -> list[list[str]] | None:
    rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            return None
        if re.match(r"^\|[-:\s|]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows if rows else None


def build_system_report_pdf(output: Path) -> None:
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
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=14)
    code_style = ParagraphStyle("Code", parent=body, fontName="Courier", fontSize=8, leading=10)

    story: list = []
    in_code = False
    in_mermaid = False
    code_lines: list[str] = []
    table_buffer: list[str] = []

    def flush_code() -> None:
        nonlocal code_lines, in_code, in_mermaid
        if code_lines:
            block = "\n".join(code_lines)
            story.append(Preformatted(block, code_style))
            story.append(Spacer(1, 0.08 * inch))
        code_lines = []
        in_code = False
        in_mermaid = False

    def flush_table() -> None:
        nonlocal table_buffer
        if not table_buffer:
            return
        rows = _parse_table_rows(table_buffer)
        table_buffer = []
        if not rows:
            return
        col_count = max(len(r) for r in rows)
        widths = [5.5 * inch / col_count] * col_count
        table = Table(rows, colWidths=widths)
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.08 * inch))

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_table()
            if in_code:
                flush_code()
            else:
                lang = stripped[3:].strip()
                in_code = True
                in_mermaid = lang == "mermaid"
            continue

        if in_code:
            if not in_mermaid:
                code_lines.append(line.rstrip())
            continue

        if stripped.startswith("|"):
            table_buffer.append(stripped)
            continue
        flush_table()

        if not stripped:
            story.append(Spacer(1, 0.06 * inch))
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(_clean_inline(stripped[2:]), h1))
        elif stripped.startswith("## "):
            story.append(Paragraph(_clean_inline(stripped[3:]), h2))
        elif stripped.startswith("### "):
            story.append(Paragraph(_clean_inline(stripped[4:]), h3))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 0.1 * inch))
        elif stripped.startswith("- "):
            story.append(Paragraph(f"&bull; {_clean_inline(stripped[2:])}", body))
        elif re.match(r"^\d+\.\s", stripped):
            story.append(Paragraph(_clean_inline(stripped), body))
        else:
            story.append(Paragraph(_clean_inline(stripped), body))

    flush_table()
    flush_code()

    metrics = _load_live_metrics()
    story.append(PageBreak())
    story.append(Paragraph("Appendix A: Live Evaluation Metrics", h2))
    story.append(Spacer(1, 0.1 * inch))
    story += metrics_table_slide(metrics)[:-1]  # drop page break

    if HEART_CHART.exists():
        story.append(PageBreak())
        story.append(Paragraph("Appendix B: HEART Metrics Chart", h2))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Image(str(HEART_CHART), width=6 * inch, height=3.3 * inch))
    if RETENTION_CHART.exists():
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Appendix C: Cohort Retention Curve", h2))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Image(str(RETENTION_CHART), width=6 * inch, height=3.3 * inch))

    doc.build(story)
    print(f"Created {output}")


def main() -> None:
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    charts_script = ROOT / "scripts" / "generate_charts.py"
    if charts_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(charts_script)], check=False)
    metrics = _load_live_metrics()
    build_presentation_pdf(SUBMISSION_DIR / "Task-3-Presentation.pdf", metrics)
    build_system_report_pdf(SUBMISSION_DIR / "SYSTEM_REPORT.pdf")


if __name__ == "__main__":
    main()
