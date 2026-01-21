# SANCHALAN Backend Server Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting SANCHALAN Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Current directory: $PWD" -ForegroundColor Green
Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file in the backend directory" -ForegroundColor Red
    Write-Host ""
}

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
