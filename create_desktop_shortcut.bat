@echo off
setlocal enabledelayedexpansion

:: Create Desktop Shortcut for Battery Cycle Analyzer (Windows)

echo =========================================
echo    Creating Desktop Shortcut
echo =========================================
echo.

:: Get the current directory
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Get the desktop path
for /f "tokens=3*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"

if not defined DESKTOP (
    set "DESKTOP=%USERPROFILE%\Desktop"
)

:: Create a VBScript to create the shortcut
set "VBS_FILE=%TEMP%\CreateShortcut.vbs"

echo Creating shortcut script...

(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%DESKTOP%\Battery Cycle Analyzer.lnk"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "%CURRENT_DIR%\launch_battery_analyzer.bat"
echo oLink.WorkingDirectory = "%CURRENT_DIR%"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 13"
echo oLink.Description = "Launch Battery Cycle Analyzer"
echo oLink.Save
) > "%VBS_FILE%"

:: Run the VBScript
cscript //nologo "%VBS_FILE%"

:: Clean up
del "%VBS_FILE%"

if exist "%DESKTOP%\Battery Cycle Analyzer.lnk" (
    echo.
    echo =========================================
    echo    SUCCESS!
    echo =========================================
    echo.
    echo Desktop shortcut created successfully!
    echo You can now launch Battery Cycle Analyzer from your desktop.
    echo.
) else (
    echo.
    echo ERROR: Failed to create desktop shortcut
    echo.
)

:: Also create a Start Menu shortcut
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

set "VBS_FILE=%TEMP%\CreateStartMenuShortcut.vbs"

(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%START_MENU%\Battery Cycle Analyzer.lnk"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "%CURRENT_DIR%\launch_battery_analyzer.bat"
echo oLink.WorkingDirectory = "%CURRENT_DIR%"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 13"
echo oLink.Description = "Launch Battery Cycle Analyzer"
echo oLink.Save
) > "%VBS_FILE%"

cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%"

if exist "%START_MENU%\Battery Cycle Analyzer.lnk" (
    echo Start Menu shortcut also created!
    echo.
)

pause