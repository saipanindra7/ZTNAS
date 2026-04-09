$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "backend")

if (-not (Test-Path "venv\\Scripts\\python.exe")) {
    Write-Host "Virtual environment not found at backend\\venv" -ForegroundColor Yellow
    Write-Host "Create it first: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/3] Running Bandit security scan..." -ForegroundColor Cyan
.\\venv\\Scripts\\python.exe -m bandit -r app utils -q

Write-Host "[2/3] Running Safety dependency scan..." -ForegroundColor Cyan
.\\venv\\Scripts\\python.exe -m safety check -r requirements.txt

Write-Host "[3/3] Running focused auth smoke checks..." -ForegroundColor Cyan
.\\venv\\Scripts\\python.exe -m pytest tests\\test_auth.py -q

Write-Host "Security checks completed." -ForegroundColor Green
