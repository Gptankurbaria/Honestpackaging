@echo off
echo ==========================================
echo      UPDATING WEBSITE TO CLOUD
echo ==========================================
echo.

:: Ensure we are in the correct drive and folder
E:
cd "E:\0 Prexa\BOX Costing"

:: 0. Configure Git Identity (Fixes 'Author identity unknown' error)
:: We set this locally for this folder only.
git config user.email "auto@honestpackaging.com"
git config user.name "Honest Packaging Admin"

:: 1. Check/Fix Git Repo
if not exist ".git" (
    echo [Notice] No Git repository found. Creating one...
    git init
    git branch -M main
    git remote add origin https://github.com/Gptankurbaria/Honestpackaging.git
) else (
    :: Ensure remote is valid just in case
    git remote add origin https://github.com/Gptankurbaria/Honestpackaging.git 2>NUL
)

echo [1/3] Adding files...
git add .

echo [2/3] Saving changes...
git commit -m "Update from One-Click Script"

echo [3/3] Uploading to GitHub...
git push -u origin main

echo.
echo ==========================================
echo SUCCESS! Website will check for updates.
echo (It usually takes 2 minutes to show online)
echo ==========================================
pause
