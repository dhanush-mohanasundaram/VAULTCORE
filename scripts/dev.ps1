# VAULTCORE Backend Dev Script
# Runs in PowerShell

$ErrorActionPreference = "Stop"

cd "E:\MY GOAL\PROJECTS\VAULTCORE\backend"

# Set required environment variables
$env:SECRET_KEY = "dev-secret-key-that-is-at-least-32-chars-long!!"
$env:DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5432/vaultcore"
$env:CORS_ORIGINS = "http://localhost:5173"
$env:VAULTCORE_LOW_STOCK_THRESHOLD = "5"

Write-Host "🚀 Starting VAULTCORE backend..." -ForegroundColor Green
uv run uvicorn app.main:app --reload --port 8000
