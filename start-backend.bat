@echo off
REM Start the backend API server

echo.
echo ===============================================
echo Starting ZUS Drinkware API Server
echo ===============================================
echo.

REM Check if .env.backend exists
if not exist .env.backend (
    echo ❌ .env.backend not found!
    echo Please create .env.backend with your API keys
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    exit /b 1
)

echo Starting API on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python api_server.py
