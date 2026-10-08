@echo off
title Research Paper RAG Launcher
echo ============================================
echo   Starting Research Paper RAG System...
echo ============================================

:: Start the backend in a new window
start "RAG Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

:: Wait a few seconds for backend to boot
timeout /t 5 /nobreak >nul

:: Start the frontend in a new window
start "RAG Frontend" cmd /k "cd /d %~dp0frontend && python -m http.server 3000"

:: Wait a moment, then open the browser
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo  Backend  : http://localhost:8000
echo  Frontend : http://localhost:3000
echo  API Docs : http://localhost:8000/docs
echo.
echo  Close the two server windows to stop the app.
exit