@echo off
title Battery Cycle Analyzer - Quick Start
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                Battery Cycle Analyzer - Quick Start          ║
echo ║                    Setting up environment...                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Change to the script directory (project root)
cd /d "%~dp0"

echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not found in PATH!
    echo.
    echo Please install Python from: https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo After installing Python, restart your computer and try again.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detected successfully!

echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [INFO] Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing requirements...
pip install -r config\requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Failed to install requirements!
    echo.
    echo This might be due to:
    echo • Internet connection issues
    echo • Antivirus blocking pip
    echo • Missing Microsoft Visual C++ Build Tools
    echo.
    pause
    exit /b 1
)

echo [INFO] All dependencies installed successfully!
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  🔋 Battery Cycle Analyzer is starting...                   ║
echo ║                                                              ║
echo ║  • Your web browser will open automatically                  ║
echo ║  • The application will be available at:                     ║
echo ║    http://localhost:8502                                     ║
echo ║                                                              ║
echo ║  • To stop the application: Press Ctrl+C                     ║
echo ║  • To restart: Run this script again                         ║
echo ║                                                              ║
echo ║  ⚠️ Keep this window open while using the app               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Open browser after a delay
start "" timeout /t 3 /nobreak >nul 2>&1 && start "" "http://localhost:8502"

REM Start Streamlit with port 8502 to avoid permission issues
streamlit run src\gui.py --server.port 8502 --server.headless true --browser.gatherUsageStats false

echo.
echo [INFO] Application stopped.
pause 