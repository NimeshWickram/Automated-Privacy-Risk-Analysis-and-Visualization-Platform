@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Starting PrivacyGuard Platform (Backend + Frontend)
echo ===================================================

REM Resolve Python
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "%LOCALAPPDATA%\Temp\privacyguard-phase1-python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Temp\privacyguard-phase1-python312\python.exe"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 set "PYTHON_EXE=python"
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python runtime not found.
    pause
    exit /b 1
)

REM Resolve Node
set "NODE_EXE="
if exist "%LOCALAPPDATA%\Temp\privacyguard-phase1-node\node-v22.16.0-win-x64\node.exe" (
    set "NODE_EXE=%LOCALAPPDATA%\Temp\privacyguard-phase1-node\node-v22.16.0-win-x64\node.exe"
) else (
    where node >nul 2>nul
    if %ERRORLEVEL% equ 0 set "NODE_EXE=node"
)

if "%NODE_EXE%"=="" (
    echo [ERROR] Node runtime not found.
    pause
    exit /b 1
)

echo [1/2] Launching Backend on http://127.0.0.1:8000 ...
start "PrivacyGuard Backend" cmd /k ""%PYTHON_EXE%" -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000"

echo [2/2] Launching Frontend on http://127.0.0.1:5173 ...
start "PrivacyGuard Frontend" cmd /k ""%NODE_EXE%" .\node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173"

echo.
echo ===================================================
echo Both services are starting in separate windows.
echo Frontend: http://127.0.0.1:5173
echo Backend:  http://127.0.0.1:8000
echo ===================================================
