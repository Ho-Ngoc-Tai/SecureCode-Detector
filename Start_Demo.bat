@echo off
title Defect-Scanner AI - Master's Thesis
color 0B
echo =======================================================
echo          DEFECT-SCANNER AI - MASTER'S THESIS
echo =======================================================
echo.
echo [1/2] Kiem tra va khoi dong Server...
cd /d "%~dp0demo\backend"
echo [2/2] Dang mo trinh duyet Web (Port 8080)...
start http://127.0.0.1:8080
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080
pause
