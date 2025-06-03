@echo off

REM Battery Cycle Analyzer Setup Script for Windows
REM This script sets up the virtual environment and installs dependencies

echo 🔋 Battery Cycle Analyzer Setup
echo ================================

REM Change to project root (one level up from tools)
cd /d "%~dp0"
cd ..

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=2" %%i in ('python --version') do echo ✅ Found Python %%i

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r ..\requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo 1. Run quick_start.bat (recommended), OR
echo 2. Manually:
echo    - Activate the virtual environment: venv\Scripts\activate
echo    - Change to src directory: cd src
echo    - Run the application: streamlit run gui.py
echo    - Open your browser to the displayed URL (typically http://localhost:8501)
echo.
echo To deactivate the virtual environment later, run: deactivate
pause 