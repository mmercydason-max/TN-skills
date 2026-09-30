#!/usr/bin/env bash
# Starts the FastAPI backend (port 8000) and the Streamlit UI (port 8501).
cd "$(dirname "$0")" || exit 1
if [ -f venv/bin/activate ]; then source venv/bin/activate
elif [ -f venv/Scripts/activate ]; then source venv/Scripts/activate; fi

uvicorn legalEaseAPI.main:app --port "${API_PORT:-8000}" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
sleep 2
streamlit run frontend/app.py
