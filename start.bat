@echo off
title CloudHero - Starting...
color 1F

echo.
echo  ========================================
echo    ☁  CloudHero - Cloud Security App
echo  ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python from https://python.org
    pause
    exit /b
)

echo  [1/3] Installing dependencies...
pip install flask --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo  [2/3] Starting Flask server...
start "" python app.py

echo  [3/3] Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start "" http://localhost:5000

echo.
echo  ✅ CloudHero is running at http://localhost:5000
echo  Close this window to stop the server.
echo.
pause
