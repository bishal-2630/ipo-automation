@echo off
title IPO Status - Local Check (Headed)
cd /d "%~dp0"
echo Activating virtual environment...
call venv\Scripts\activate
echo Checking IPO Status in VISIBLE mode...
set HEADLESS=false
set RUN_MODE=check_status
python main.py
pause
