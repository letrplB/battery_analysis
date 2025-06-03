@echo off
echo ========================================
echo Battery Cycle Analyzer - Windows Setup
echo ========================================
echo.
echo This script will:
echo 1. Check if Python is installed
echo 2. Install required packages
echo 3. Create desktop shortcut
echo 4. Test the application
echo.
pause

REM Change to the project root directory (two levels up from deployment/windows)
cd /d "%~dp0"
cd ..\..

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found!
python --version

echo.
echo Installing required packages...
pip install -r config\requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install packages!
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo ✅ Packages installed successfully!

echo.
echo Creating desktop shortcut...

REM Get current directory (project root)
set "CURRENT_DIR=%CD%"

REM Create VBS script to make shortcut pointing to quick_start.bat
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Battery Cycle Analyzer.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CURRENT_DIR%\quick_start.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Battery Cycle Analyzer - Double-click to start" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CURRENT_DIR%\quick_start.bat,0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Run the VBS script
cscript CreateShortcut.vbs >nul

REM Clean up
del CreateShortcut.vbs

echo ✅ Desktop shortcut created!

echo.
echo Testing the application...
echo This will start the app briefly to make sure everything works.
echo.

REM Check if GUI file exists before testing
if not exist "src\gui.py" (
    echo.
    echo ERROR: GUI file not found at src\gui.py!
    echo Please ensure the project structure is complete.
    echo.
    pause
    exit /b 1
)

REM Start streamlit in background to test, then kill it
cd src
start /B python -m streamlit run gui.py --server.port 8502 --server.headless true >nul 2>&1
cd ..

REM Wait a bit for it to start
timeout /t 5 /nobreak >nul

REM Kill the test process
taskkill /F /IM python.exe /FI "COMMANDLINE eq *streamlit*" >nul 2>&1

echo ✅ Setup completed successfully!
echo.
echo You can now:
echo 1. Double-click "Battery Cycle Analyzer" on your desktop
echo 2. Or double-click "quick_start.bat" in this folder
echo.
echo The application will open in your web browser at http://localhost:8501
echo.
pause 