@echo off
setlocal enabledelayedexpansion

:: Battery Cycle Analyzer Launcher for Windows
:: This script handles venv setup, dependency installation, and app launch

echo =========================================
echo    Battery Cycle Analyzer Launcher
echo =========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

:: Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment found.
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found.
    echo Creating virtual environment...
    python -m venv venv
    
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo.
    echo Installing dependencies...
    echo This may take a few minutes on first run...
    
    :: Upgrade pip first
    python -m pip install --upgrade pip
    
    :: Install from requirements.txt if it exists
    if exist "requirements.txt" (
        pip install -r requirements.txt
    ) else (
        :: Install manually if requirements.txt doesn't exist
        pip install streamlit pandas numpy scipy plotly openpyxl xlsxwriter chardet
    )
    
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    
    echo.
    echo =========================================
    echo    Installation complete!
    echo =========================================
)

:: Navigate to battery_cycle_analyzer
cd battery_cycle_analyzer

:: Check if the package directory exists
if not exist "src\gui_modular.py" (
    echo ERROR: Cannot find battery_cycle_analyzer\src\gui_modular.py
    echo Please make sure you're running this from the battery_analysis root directory
    pause
    exit /b 1
)

:: Start the application
echo.
echo Starting Battery Cycle Analyzer...
echo.
echo The application will open in your default browser.
echo If it doesn't open automatically, navigate to: http://localhost:8501
echo.
echo =========================================
echo    Press Ctrl+C to stop the application
echo =========================================
echo.

:: Run Streamlit
streamlit run src\gui_modular.py

:: When user stops the app
echo.
echo =========================================
echo    Application stopped
echo =========================================
echo.
pause