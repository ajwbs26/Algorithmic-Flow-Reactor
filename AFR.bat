@echo off

cd /d C:\Users\Administrator\Documents\AFR

call venv\Scripts\activate

start "AFR LIVE ENGINE" cmd /k python live\paper_engine.py

timeout /t 3 >nul

echo.
echo ============================
echo AFR STARTED
echo ============================
echo.
pause