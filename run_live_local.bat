@echo off
title IPO Automation - Live Apply (Headed)
cd /d "%~dp0"
echo Activating virtual environment...
call venv\Scripts\activate
echo Starting IPO Automation in VISIBLE mode...
set HEADLESS=false
set RUN_MODE=apply
python main.py
pause
