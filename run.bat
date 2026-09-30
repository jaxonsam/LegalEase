@echo off
REM Windows: opens the backend in a new window, then starts the frontend here.
start "LegalEase Backend" cmd /k "venv\Scripts\activate && uvicorn legalEaseAPI.main:app --reload --port 8000"
timeout /t 3 >nul
call venv\Scripts\activate
streamlit run frontend/app.py
