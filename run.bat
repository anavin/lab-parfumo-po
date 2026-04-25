@echo off
cd /d "%~dp0"

echo.
echo ==========================================
echo  Lab Parfumo PO Pro System
echo ==========================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] not found Python
    pause
    exit /b 1
)

python -c "import streamlit, supabase, reportlab, pandas, PIL, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

echo.
echo Starting web server...
python -m streamlit run app.py

if %errorlevel% neq 0 pause
