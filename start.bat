@echo off
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set POLL_INTERVAL=10
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
