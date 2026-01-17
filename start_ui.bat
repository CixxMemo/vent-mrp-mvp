@echo off
cd /d %~dp0
set API_URL=http://localhost:8000
streamlit run streamlit_app.py

