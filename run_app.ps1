# ========================================================
# Script khoi dong toan bo he thong DocuCTSV tren Windows PowerShell
# ========================================================
$ErrorActionPreference = "Stop"
$WorkspaceRoot = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  DANG KHOI DONG TOAN BO DU AN DOCUCTSV (DAI HOC DA LAT)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
if (-not (Test-Path $PythonExe)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $PythonExe = $cmd.Source
    } else {
        $PythonExe = "python"
    }
}

# 1. Khoi dong Backend FastAPI
Write-Host "[1/2] Dang khoi dong Backend FastAPI (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\backend'; & '$PythonExe' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# 2. Khoi dong Frontend Vite React
Write-Host "[2/2] Dang khoi dong Frontend React Vite (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "  HE THONG DA KHOI DONG HOAN TAT!" -ForegroundColor Green
Write-Host "  - Frontend Web UI:      http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  - API Health Check:     http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
