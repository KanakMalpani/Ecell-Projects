#!/usr/bin/env python
"""Generate a sample PDF document for demo ingestion."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    print("Install reportlab: pip install reportlab")
    sys.exit(1)

OUTPUT = ROOT / "data" / "raw" / "backup_recovery_sop.pdf"

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

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUTPUT), pagesize=letter)
width, height = letter
y = height - 72
for line in CONTENT:
    c.drawString(72, y, line[:90])
    y -= 16
    if y < 72:
        c.showPage()
        y = height - 72
c.save()
print(f"Created {OUTPUT}")
