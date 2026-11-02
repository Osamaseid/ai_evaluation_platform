@echo off
echo ===============================================================
echo Starting AutoGrade AI in Development Mode (Vite Hot-Reload)
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo ===============================================================

start "AutoGrade Backend" .\.venv\Scripts\uvicorn evaluator.api.app:app --host 127.0.0.1 --port 8000 --reload
cd frontend
start "" http://localhost:5173
cmd /c pnpm run dev

