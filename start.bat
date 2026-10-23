@echo off
echo ========================================================
echo   Starting AI Task Management Agent (Full-Stack Environment)
echo ========================================================

cd /d "%~dp0"

echo [1/2] Starting Python AI Logic API Server on http://localhost:8000...
start "AI Task Agent API" cmd /k "start_api.bat"

echo [2/2] Starting Frontend Vite UI Server...
if exist "ai-task-management-ui" (
    cd ai-task-management-ui
    start "AI Task Management UI" cmd /k "npm run dev"
) else (
    echo Note: ai-task-management-ui not found, starting local frontend...
)

echo Both services launched! Access the UI at http://localhost:5173
pause
