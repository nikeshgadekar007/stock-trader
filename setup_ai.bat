@echo off
REM Stock Trading AI Setup - Python + TensorFlow
REM Run this to enable CNN-LSTM deep learning model

echo ========================================
echo Stock Trading AI Setup
echo ========================================
echo.
echo This script will:
echo 1. Check for Python 3.9-3.12
echo 2. Create virtual environment
echo 3. Install TensorFlow and dependencies
echo 4. Enable CNN-LSTM model
echo.

REM Check for Python using py launcher
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python 3.11 via py launcher!
    set PYTHON_CMD=py -3.11
    goto :create_venv
)

py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python 3.10 via py launcher!
    set PYTHON_CMD=py -3.10
    goto :create_venv
)

py -3.9 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python 3.9 via py launcher!
    set PYTHON_CMD=py -3.9
    goto :create_venv
)

echo ERROR: No Python 3.9-3.12 found!
echo.
echo Please install Python 3.11:
echo 1. Go to https://www.python.org/downloads/
echo 2. Download Python 3.11.x
echo 3. IMPORTANT: Check "Add Python to PATH"
echo 4. Run this script again
echo.
pause
exit /b 1

:create_venv
echo.
echo Creating virtual environment with %PYTHON_CMD%...
%PYTHON_CMD% -m venv venv_ai

REM Activate virtual environment
echo Activating virtual environment...
call venv_ai\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install TensorFlow and dependencies
echo Installing TensorFlow (this may take a while)...
pip install tensorflow>=2.15.0

echo Installing other dependencies...
pip install yfinance pandas numpy plotly streamlit scikit-learn

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To activate the AI environment:
echo   call venv_ai\Scripts\activate.bat
echo.
echo To run the app with AI:
echo   streamlit run app.py
echo.
echo To train the CNN-LSTM model:
echo   python train_model.py
echo.
pause