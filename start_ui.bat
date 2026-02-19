@echo off
cd /d %~dp0
set API_URL=http://localhost:8000
streamlit run streamlit_app.py --server.headless true --server.runOnSave false --server.fileWatcherType none --browser.gatherUsageStats false --server.port 8501 --server.address 127.0.0.1

