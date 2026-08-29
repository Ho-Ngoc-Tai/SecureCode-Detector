@echo off
title Defect-Scanner AI - Master's Thesis
color 0B
echo =======================================================
echo          DEFECT-SCANNER AI - MASTER'S THESIS
echo =======================================================
echo.
echo [1/2] Kiem tra va khoi dong Server...
cd /d "%~dp0demo\backend"
echo [2/2] Dang mo trinh duyet Web...
start http://127.0.0.1:8000
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
