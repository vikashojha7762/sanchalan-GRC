@echo off
echo ========================================
echo Starting SANCHALAN Backend Server
echo ========================================
echo.
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Starting server on http://localhost:8000
echo Press CTRL+C to stop the server
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
