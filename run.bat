@echo off
REM Starts the backend and the frontend in two windows (Windows).
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
  echo Virtual environment not found. Run: python -m venv venv
  exit /b 1
)
start "LegalEase API" cmd /k "venv\Scripts\activate.bat && uvicorn legalEaseAPI.main:app --reload --port 8000"
timeout /t 3 >nul
start "LegalEase UI" cmd /k "venv\Scripts\activate.bat && streamlit run frontend\app.py"
