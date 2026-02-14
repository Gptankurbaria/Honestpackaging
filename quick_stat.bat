@echo off
title Box Costing - Quick Stats
color 0B
cls
echo ========================================
echo        BOX COSTING QUICK STATS
echo ========================================
echo.
echo Checking environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python to see full stats.
    pause
    exit /b
)

python quick_stats.py
echo.
echo Press any key to refresh or Ctrl+C to exit...
pause >nul
goto :top

:top
cls
python quick_stats.py
echo.
echo Last updated: %date% %time%
echo Press any key to refresh or Ctrl+C to exit...
pause >nul
goto :top
