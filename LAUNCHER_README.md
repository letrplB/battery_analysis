# Battery Cycle Analyzer - Launcher Guide

This guide explains how to use the launcher scripts to easily run the Battery Cycle Analyzer without terminal knowledge.

## Quick Start

### Windows Users

1. **First Time Setup:**
   - Double-click `create_desktop_shortcut.bat`
   - This creates a desktop shortcut

2. **Running the App:**
   - Double-click the "Battery Cycle Analyzer" shortcut on your desktop
   - Or double-click `launch_battery_analyzer.bat` directly

### Mac Users

1. **First Time Setup:**
   - Double-click `create_desktop_shortcut.sh`
   - If it doesn't run, right-click → Open With → Terminal
   - This creates an app on your desktop

2. **Running the App:**
   - Double-click the "Battery Cycle Analyzer" app on your desktop
   - Or double-click `launch_battery_analyzer.sh` in Terminal

### Linux Users

1. **First Time Setup:**
   - Run: `./create_desktop_shortcut.sh`
   - This creates a desktop shortcut and menu entry

2. **Running the App:**
   - Double-click the desktop shortcut
   - Or run: `./launch_battery_analyzer.sh`

### All Platforms (Python)

You can also use the cross-platform Python launcher:
```bash
python launch_battery_analyzer.py
```

## What the Launchers Do

The launcher scripts automatically:

1. **Check Python Installation** - Verify Python 3.8+ is installed
2. **Create Virtual Environment** - Set up an isolated Python environment (first run only)
3. **Install Dependencies** - Download and install all required packages (first run only)
4. **Launch Application** - Start the Battery Cycle Analyzer
5. **Open Browser** - Automatically open the app in your default browser

## Features

### Smart Detection
- Checks if virtual environment exists
- Skips installation if already set up
- Reuses existing environment on subsequent runs

### Error Handling
- Clear error messages if Python is missing
- Installation progress feedback
- Helpful troubleshooting hints

### User-Friendly
- No terminal knowledge required
- One-click launch after initial setup
- Desktop shortcuts for easy access

## File Descriptions

| File | Platform | Purpose |
|------|----------|---------|
| `launch_battery_analyzer.bat` | Windows | Main launcher script |
| `launch_battery_analyzer.sh` | Mac/Linux | Main launcher script |
| `launch_battery_analyzer.py` | All | Cross-platform Python launcher |
| `create_desktop_shortcut.bat` | Windows | Creates desktop shortcut |
| `create_desktop_shortcut.sh` | Mac/Linux | Creates desktop app/shortcut |

## System Requirements

- **Python 3.8 or higher** must be installed
- **Internet connection** for first-time package installation
- **~500 MB disk space** for virtual environment and packages

## Troubleshooting

### "Python is not installed"
- Download Python from https://python.org
- **Windows**: Check "Add Python to PATH" during installation
- **Mac**: Install using Homebrew: `brew install python3`
- **Linux**: Use package manager: `sudo apt-get install python3`

### "Cannot find battery_cycle_analyzer"
- Make sure you're running the launcher from the `battery_analysis` root directory
- The launcher must be in the same directory as the `battery_cycle_analyzer` folder

### Application won't start
- Check if port 8501 is already in use
- Try closing other Streamlit applications
- Check the terminal for specific error messages

### Browser doesn't open
- Manually navigate to http://localhost:8501
- Try a different browser
- Check firewall settings

## How to Stop the Application

### Windows
- Press `Ctrl+C` in the terminal window
- Or close the terminal window

### Mac/Linux
- Press `Ctrl+C` in the terminal
- Or close the terminal window

## Advanced Options

### Using a Different Port
Edit the launcher script and add `--server.port 8502` to the streamlit command:
```bash
streamlit run src/gui_modular.py --server.port 8502
```

### Custom Python Path
If Python is not in PATH, edit the launcher to use full path:
```bash
C:\Python39\python.exe  # Windows example
/usr/local/bin/python3  # Mac/Linux example
```

### Development Mode
For development with auto-reload:
```bash
streamlit run src/gui_modular.py --server.runOnSave true
```

## Security Note

The launchers create a virtual environment to isolate dependencies from your system Python. This is a best practice that:
- Prevents conflicts with other Python projects
- Keeps your system Python clean
- Makes the application portable

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify Python is installed: `python --version`
3. Check the logs in `battery_cycle_analyzer/logs/`
4. Create an issue on GitHub with:
   - Your operating system
   - Python version
   - Error messages
   - Steps to reproduce