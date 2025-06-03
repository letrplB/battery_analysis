# 🔋 Battery Cycle Analyzer

A Python-based tool for analyzing battery cycle stability data from Basytec Battery Test System files.

## 🚀 Quick Start

### **Easiest Method (Recommended)**

1. **Windows**: Double-click `quick_start.bat`
2. **Mac/Linux**: Run `python3 quick_start.py`

That's it! The application will:
- ✅ Create a virtual environment automatically
- ✅ Install all dependencies 
- ✅ Open in your web browser at http://localhost:8501

### **Alternative Methods**

- **Windows Setup**: Run `deployment/windows/setup_windows.bat` for one-time setup
- **Cross-Platform**: Use `deployment/cross_platform/launch.py`
- **PowerShell**: Run `deployment/windows/run_battery_analyzer.ps1`

## 📋 Requirements

- Python 3.8 or higher
- Internet connection (for first-time setup only)

## 📁 Project Structure

```
battery_cycle_analyzer/
├── quick_start.bat          # ⭐ Main Windows launcher
├── quick_start.py           # ⭐ Main cross-platform launcher
├── src/
│   ├── gui.py              # Web interface
│   └── analyzer.py         # Analysis engine
├── config/
│   └── requirements.txt    # Dependencies
├── deployment/             # Alternative launchers
└── docs/                   # Documentation
```

## 📖 Usage

1. Start the application using one of the quick start methods above
2. Upload your Basytec data file (.txt or .csv)
3. Set analysis parameters (weight, C-rates, etc.)
4. Click "Analyze Data"
5. View results and download CSV

## 📚 Documentation

- `LAUNCHER_GUIDE.md` - Detailed guide to all launcher options
- `docs/README.md` - Full documentation
- `docs/README_WINDOWS.md` - Windows-specific instructions

## 🆘 Troubleshooting

If you encounter issues:

1. **Python not found**: Install Python from [python.org](https://python.org) and make sure to check "Add to PATH"
2. **Package errors**: Delete the `venv` folder and run the quick start script again
3. **Port in use**: Close other instances or change the port in the launcher script

For more help, see the documentation in the `docs/` folder. 