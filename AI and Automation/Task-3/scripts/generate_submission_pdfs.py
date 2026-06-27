#!/usr/bin/env python
"""
Generate submission PDFs for Task 3: presentation deck and system report.

Outputs in submission/:
  - Task-3-Presentation.pdf
  - SYSTEM_REPORT.pdf

Run: python scripts/generate_charts.py && python scripts/generate_submission_pdfs.py
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
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

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


def build_presentation_pdf(output: Path) -> None:
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
            "1,050 support tickets with full lifecycle states",
            "2,500 interaction logs spanning ~6 months",
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

    # Charts slide (if generated from live data)
    if HEART_CHART.exists():
        styles = getSampleStyleSheet()
        story.append(Paragraph("Evaluation Metrics (Live Data)", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))
        img_w = 5.5 * inch
        story.append(Image(str(HEART_CHART), width=img_w, height=img_w * 0.55))
        if RETENTION_CHART.exists():
            story.append(Spacer(1, 0.1 * inch))
            story.append(Image(str(RETENTION_CHART), width=img_w, height=img_w * 0.55))
        story.append(PageBreak())

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
            "Source code: AI and Automation/Task-3/",
            "System report: SYSTEM_REPORT.md + submission/SYSTEM_REPORT.pdf",
            "Presentation: submission/Task-3-Presentation.pdf",
            "Demo credentials documented in README (demo-only passwords)",
        ],
    )

    doc.build(story)
    print(f"Created {output}")


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

    def flush_code() -> None:
        nonlocal code_lines, in_code, in_mermaid
        if code_lines:
            block = "\n".join(code_lines)
            block = block.replace("──►", "->").replace("│", "|").replace("▼", "v").replace("┌", "+").replace("┐", "+").replace("└", "+").replace("┘", "+")
            story.append(Preformatted(block, code_style))
            story.append(Spacer(1, 0.08 * inch))
        code_lines = []
        in_code = False
        in_mermaid = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                flush_code()
            else:
                lang = stripped[3:].strip()
                in_code = True
                in_mermaid = lang == "mermaid"
            continue

        if in_code:
            if in_mermaid:
                continue  # skip mermaid diagrams in PDF
            code_lines.append(line.rstrip())
            continue

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
        elif stripped.startswith("|") and "---" not in stripped:
            safe = _clean_inline(stripped)
            story.append(Paragraph(f"<font face='Courier' size='8'>{safe}</font>", body))
        elif stripped.startswith("- "):
            story.append(Paragraph(f"&bull; {_clean_inline(stripped[2:])}", body))
        elif re.match(r"^\d+\.\s", stripped):
            story.append(Paragraph(_clean_inline(stripped), body))
        else:
            story.append(Paragraph(_clean_inline(stripped), body))

    flush_code()

    if HEART_CHART.exists():
        story.append(PageBreak())
        story.append(Paragraph("Appendix: HEART Metrics Chart", h2))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Image(str(HEART_CHART), width=6 * inch, height=3.3 * inch))
    if RETENTION_CHART.exists():
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Appendix: Cohort Retention Curve", h2))
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
    build_presentation_pdf(SUBMISSION_DIR / "Task-3-Presentation.pdf")
    build_system_report_pdf(SUBMISSION_DIR / "SYSTEM_REPORT.pdf")


if __name__ == "__main__":
    main()
