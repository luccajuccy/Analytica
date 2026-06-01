@echo off
setlocal
cd /d "%~dp0"
echo Iniciando Analytica em http://localhost:5000
"%~dp0venv\Scripts\python.exe" AnalyticaSync.py
