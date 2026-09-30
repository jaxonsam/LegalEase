#!/usr/bin/env bash
# Linux/Mac: starts backend + frontend. On Windows use run.bat
uvicorn legalEaseAPI.main:app --reload --port 8000 &
sleep 2
streamlit run frontend/app.py
