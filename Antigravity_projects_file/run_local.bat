@echo off
title MediSafe AI Server
echo ===================================================
echo Starting MediSafe AI Web Application...
echo ===================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Using Virtual Environment (.venv)...
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo Virtual environment not found. Using system Python...
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
)

pause
