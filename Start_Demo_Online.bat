@echo off
title Defect-Scanner AI - Master's Thesis (Online Cloudflare Demo)
color 0A
echo =======================================================
echo     DEFECT-SCANNER AI - ONLINE CLOUDFLARE LAUNCHER
echo =======================================================
echo.
cd /d "%~dp0demo\backend"
python run_online.py
pause
