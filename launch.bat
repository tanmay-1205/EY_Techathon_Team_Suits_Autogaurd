@echo off
echo ========================================
echo  AutoGuard Fleet Management System
echo  Starting Dashboard...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo Starting Streamlit dashboard...
echo Dashboard will open in your browser automatically.
echo.
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

REM Run Streamlit
streamlit run src/dashboard_enhanced.py

pause
