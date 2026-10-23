@echo off
echo ===================================================
echo   Starting AI Task Management Agent - Python API
echo ===================================================

cd /d "%~dp0"

:: Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python api_server.py
pause
