@echo off
title BOX Costing - Dashboard Launcher
color 0A
cls
echo ========================================
echo       BOX COSTING DASHBOARD
echo ========================================
echo.
echo Checking for Python and Streamlit...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Try to run streamlit. If it fails, suggest installing requirements.
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Streamlit not found. Attempting to install requirements...
    pip install -r requirements.txt
)

echo.
echo Launching Dashboard...
echo Close this window to stop the server.
echo.
python -m streamlit run app.py
pause
