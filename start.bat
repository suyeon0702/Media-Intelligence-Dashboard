@echo off
echo Starting Media Intelligence Dashboard...

echo [1/2] Starting backend server...
start "Backend" cmd /k "cd backend && uv run uvicorn main:app --reload --port 8000"

timeout /t 5 /nobreak > nul

echo [2/2] Starting frontend server...
start "Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak > nul

echo Opening browser...
start http://localhost:5173

echo.
echo Dashboard: http://localhost:5173
echo API Docs:  http://localhost:8000/docs
echo.
pause