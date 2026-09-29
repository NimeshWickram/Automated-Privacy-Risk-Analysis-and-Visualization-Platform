# PrivacyGuard launcher script for PowerShell
$ErrorActionPreference = "Stop"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Starting PrivacyGuard Platform (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Resolve Python
$PythonExe = $null
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonExe = (Resolve-Path ".venv\Scripts\python.exe").Path
} elseif (Test-Path "$env:LOCALAPPDATA\Temp\privacyguard-phase1-python312\python.exe") {
    $PythonExe = "$env:LOCALAPPDATA\Temp\privacyguard-phase1-python312\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
}

if (-not $PythonExe) {
    Write-Error "Python executable not found."
    exit 1
}

# Resolve Node
$NodeExe = $null
if (Test-Path "$env:LOCALAPPDATA\Temp\privacyguard-phase1-node\node-v22.16.0-win-x64\node.exe") {
    $NodeExe = "$env:LOCALAPPDATA\Temp\privacyguard-phase1-node\node-v22.16.0-win-x64\node.exe"
} elseif (Get-Command node -ErrorAction SilentlyContinue) {
    $NodeExe = "node"
}

if (-not $NodeExe) {
    Write-Error "Node executable not found."
    exit 1
}

Write-Host "[1/2] Starting FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000"

Write-Host "[2/2] Starting Vite frontend on http://127.0.0.1:5173..." -ForegroundColor Green
Start-Process -FilePath $NodeExe -ArgumentList ".\node_modules\vite\bin\vite.js", "--host", "127.0.0.1", "--port", "5173"

Write-Host "`nBoth services are now running!" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
