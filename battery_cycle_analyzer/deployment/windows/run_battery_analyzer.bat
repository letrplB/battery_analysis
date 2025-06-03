@echo off
title Battery Cycle Analyzer
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Battery Cycle Analyzer                   ║
echo ║                     Starting Application...                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Change to the project root directory (two levels up from deployment/windows)
cd /d "%~dp0"
cd ..\..

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

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Found %PYTHON_VERSION%

echo.
echo [INFO] Checking required packages...

REM Check if streamlit is installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [INFO] Installing required packages... This may take a few minutes.
    echo.
    pip install -r ..\..\requirements.txt
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install packages!
        echo.
        echo Please check your internet connection and try:
        echo   pip install -r ..\..\requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Packages installed successfully!
) else (
    echo [SUCCESS] Required packages are already installed!
)

REM Check if gui.py exists
if not exist "src\gui.py" (
    echo.
    echo [ERROR] GUI file not found!
    echo Expected location: src\gui.py
    echo Please ensure the project structure is complete.
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Battery Cycle Analyzer...
echo.
echo ┌─ INSTRUCTIONS ────────────────────────────────────────────────┐
echo │ • Your web browser will open automatically                   │
echo │ • The application will be available at:                      │
echo │   http://localhost:8502                                      │
echo │                                                               │
echo │ • To stop the application:                                    │
echo │   - Close this window, OR                                     │
echo │   - Press Ctrl+C in this window                              │
echo └───────────────────────────────────────────────────────────────┘
echo.

REM Try to open browser automatically after a delay
start "" python -c "import webbrowser, time; time.sleep(5); webbrowser.open('http://localhost:8502')" 2>nul

REM Start the Streamlit app from the src directory
echo [INFO] Launching web interface...
cd src
python -m streamlit run gui.py --server.port 8502 --server.headless true --browser.gatherUsageStats false

REM Return to project root
cd ..

REM If we get here, the app has stopped
echo.
echo [INFO] Application has been stopped.

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo [ERROR] The application encountered an error.
    echo.
    echo Common solutions:
    echo • Make sure src\gui.py exists in the project folder
    echo • Try running the quick_start.bat script instead
    echo • Check that no other application is using port 8502
    echo.
    pause
) else (
    echo.
    echo Thank you for using Battery Cycle Analyzer!
    timeout /t 3 /nobreak >nul
) 