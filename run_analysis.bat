@echo off
REM Intraday Trading Analysis - Run Script
REM Run this script daily to analyze US market stocks

echo ================================================
echo   Intraday Trading Analysis System
echo ================================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import yfinance" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Running analysis...
echo.

python main.py

echo.
echo ================================================
echo   Analysis Complete!
echo ================================================
echo.
echo Open output/analysis_report.html in your browser
echo to view the recommendations.
echo.

pause