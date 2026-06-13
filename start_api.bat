@echo off
cd /d %~dp0
uvicorn api_app:app --reload

