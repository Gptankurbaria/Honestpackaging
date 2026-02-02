@echo off
echo ==========================================
echo    ONE-CLICK SETUP & PUSH TO GITHUB
echo ==========================================
echo.

:: Ensure we are in the correct drive and folder
E:
cd "E:\0 Prexa\BOX Costing"

echo [1/5] Initializing Git...
git init
git branch -M main

echo [2/5] linking to GitHub...
:: This might show an error if already linked, which is fine.
git remote add origin https://github.com/Gptankurbaria/Honestpackaging.git

echo [3/5] Adding all files...
git add .

echo [4/5] Saving changes...
git commit -m "One-click setup and upload"

echo [5/5] Uploading to GitHub...
git push -u origin main

echo.
echo ==========================================
echo DONE! If you see 'Success' or 'main -> main' above, it worked.
echo ==========================================
pause
