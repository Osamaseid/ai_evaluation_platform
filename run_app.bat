@echo off
echo ===============================================================
echo Starting AutoGrade AI - Programming Evaluation Platform
echo Backend + Frontend SPA Unified Server on http://127.0.0.1:8000
echo ===============================================================

if not exist ".venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in .venv!
    pause
    exit /b 1
)

start "" http://127.0.0.1:8000
.\.venv\Scripts\uvicorn evaluator.api.app:app --host 127.0.0.1 --port 8000

