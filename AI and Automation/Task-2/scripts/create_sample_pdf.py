#!/usr/bin/env python
"""
=============================================================================
Sample PDF Generator — Demo Corpus Extension
=============================================================================

PURPOSE
-------
Creates a synthetic IT Standard Operating Procedure (SOP) as a PDF file so
the ingestion pipeline can be tested with an additional document beyond the
bundled .txt policy files.

ROLE IN THE RAG PIPELINE
------------------------
  NOT part of the core five-stage pipeline — this is a utility script that
  populates Stage 1's input directory (data/raw/) with demo content.

  Flow: create_sample_pdf.py → data/raw/backup_recovery_sop.pdf
        → run_ingest.py / run_pipeline.py → chunks.json → embed → query

INTERVIEW TALKING POINTS
------------------------
1. **Dynamic ingestion demo:** Shows the system handles new PDFs dropped into
   raw_dir without code changes — re-run ingest + embed to refresh the index.
2. **ReportLab vs pdfplumber:** ReportLab *generates* PDFs; pdfplumber *reads*
   them in ingest.py — complementary tools in the document lifecycle.
3. **Structured SOP content:** Sections (BACKUP SCHEDULE, RTO/RPO, RESTORE
   PROCEDURE) test heading-based segmentation in ingest.split_into_sections().
4. **Fictional but realistic:** Tier-1/2/3 RTO/RPO numbers are plausible for
   enterprise DR discussions during live Q&A demos.

USAGE:
    python scripts/create_sample_pdf.py

REQUIRES:
    pip install reportlab
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Dependency check — fail fast with install hint if reportlab missing
# ---------------------------------------------------------------------------
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    print("Install reportlab: pip install reportlab")
    sys.exit(1)

OUTPUT = ROOT / "data" / "raw" / "backup_recovery_sop.pdf"

# ---------------------------------------------------------------------------
# Demo SOP content — structured for heading detection during ingestion
# ---------------------------------------------------------------------------
# Interview note: ALL-CAPS section titles match ingest.py heading heuristics
# (isupper + short lines) so chunks get meaningful section_hint metadata.
CONTENT = [
    "STANDARD OPERATING PROCEDURE: DATA BACKUP AND RECOVERY",
    "SOP-IT-BKP-007 | Version 2.0 | Owner: Infrastructure Team",
    "",
    "1. BACKUP SCHEDULE",
    "Production databases: full backup daily at 02:00 UTC, incremental every 6 hours.",
    "File servers: nightly snapshot with 30-day retention.",
    "Critical application configs: version-controlled in Git with hourly sync.",
    "",
    "2. RECOVERY TIME OBJECTIVES",
    "Tier-1 systems (payment, auth): RTO 1 hour, RPO 15 minutes.",
    "Tier-2 systems (internal tools): RTO 4 hours, RPO 1 hour.",
    "Tier-3 systems (analytics): RTO 24 hours, RPO 24 hours.",
    "",
    "3. RESTORE PROCEDURE",
    "Step 1: Declare incident and assign recovery lead.",
    "Step 2: Identify last clean backup from backup catalog.",
    "Step 3: Restore to isolated staging environment and validate integrity.",
    "Step 4: Failover production traffic after sign-off from system owner.",
    "",
    "4. TESTING",
    "Quarterly restore drills are mandatory for all Tier-1 and Tier-2 systems.",
    "Results must be documented in the compliance audit log within 5 business days.",
]

# ---------------------------------------------------------------------------
# PDF rendering — simple letter-size canvas with line wrapping via pagination
# ---------------------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUTPUT), pagesize=letter)
width, height = letter
y = height - 72
for line in CONTENT:
    c.drawString(72, y, line[:90])  # truncate long lines to page width
    y -= 16
    if y < 72:
        c.showPage()
        y = height - 72
c.save()
print(f"Created {OUTPUT}")
