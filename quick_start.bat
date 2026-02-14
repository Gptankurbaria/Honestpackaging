@echo off
title BOX Costing - Quick Start
color 0E
cls
echo ========================================
echo       BOX COSTING QUICK START
echo ========================================
echo.
echo [1] Launch Dashboard
echo [2] View Quick Stats
echo [3] Reset Admin Password (to admin12345)
echo [4] Exit
echo.
set /p choice="Select an option (1-4): "

if "%choice%"=="1" goto launch
if "%choice%"=="2" goto stats
if "%choice%"=="3" goto reset
if "%choice%"=="4" exit
goto start

:reset
cls
echo Resetting Admin password to admin12345...
python reset_admin_password.py admin12345
pause
goto start

:launch
cls
echo Starting Streamlit Dashboard...
python -m streamlit run app.py
pause
goto start

:stats
call quick_stat.bat
goto start

:start
goto :EOF
