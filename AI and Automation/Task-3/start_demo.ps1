# Start E-Cell Task 3 CRM demo (Windows)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
    Write-Host "Edit .env and set JWT_SECRET before public use."
}

if (-not (Test-Path "data\crm.db")) {
    Write-Host "Running data pipeline..."
    .\.venv\Scripts\python run_pipeline.py --skip-generate
    if (-not (Test-Path "data\synthetic_crm_dataset.json")) {
        .\.venv\Scripts\python run_pipeline.py
    }
}

Write-Host ""
Write-Host "Starting API on http://127.0.0.1:8002"
Write-Host "  Swagger:   http://127.0.0.1:8002/docs"
Write-Host "  Dashboard: http://127.0.0.1:8002/dashboard"
Write-Host ""
Write-Host "Login: analytics1 / analytics123 (dashboard) or agent1 / agent123 (API)"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

.\.venv\Scripts\python -m uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload
