# VAULTCORE Backend Test Script
# Runs in PowerShell

$ErrorActionPreference = "Stop"

cd "E:\MY GOAL\PROJECTS\VAULTCORE\backend"

# Set required environment variables
$env:SECRET_KEY = "dev-secret-key-that-is-at-least-32-chars-long!!"
$env:DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5432/vaultcore"

Write-Host "🧪 Running VAULTCORE backend tests..." -ForegroundColor Green
uv run pytest "$@"
