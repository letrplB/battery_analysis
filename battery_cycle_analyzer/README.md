# 🔋 Battery Cycle Analyzer

A Python-based tool for analyzing battery cycle stability data from Basytec Battery Test System files. This tool provides automated parsing, cycle detection, capacity calculation, and visualization capabilities through a user-friendly web interface.

## 🚀 Quick Start

### **Recommended Method**

1. **Windows**: Double-click `quick_start.bat`
2. **Mac/Linux**: Run `python3 quick_start.py`

**That's it!** The application will:
- ✅ Create a virtual environment automatically
- ✅ Install all dependencies from the root `requirements.txt`
- ✅ Open in your web browser at http://localhost:8501

### **Alternative Methods**

- **Windows Setup**: Run `deployment/windows/setup_windows.bat` for one-time setup + desktop shortcut
- **Cross-Platform**: Use `deployment/cross_platform/launch.py`
- **PowerShell**: Run `deployment/windows/run_battery_analyzer.ps1`

## 📋 Requirements

- **Python 3.8+** - [Download from python.org](https://python.org) (check "Add to PATH" during installation)
- **Internet connection** (for first-time setup only)

## 📖 Usage

1. **Start** the application using one of the methods above
2. **Upload** your Basytec data file (.txt or .csv)
3. **Configure** analysis parameters:
   - Active material weight (grams)
   - Theoretical capacity (Ah)
   - C-rate configurations (auto-detected from test plans)
4. **Click "Analyze"** to process your data
5. **View results** and download CSV files

## 📁 Supported File Format

### **Basytec Battery Test System Files**

The tool expects files with:
- **Metadata headers** starting with `~`
- **Space/tab-separated** data columns
- **Required columns**: `Time[h]`, `Command`, `U[V]`, `I[A]`, `State`

**Example file structure:**
```
~Resultfile from Basytec Battery Test System
~Date and Time of Data Converting: 19.05.2025 14:36:50
~Name of Test: KM_KMFO_721_F1_E5 50mAhg 2xF 05052025
~Battery: KM-KMFO-721-F1E5(16) 50mAh 2xF
~
~Time[h] DataSet DateTime t-Step[h] Command U[V] I[A] State ...
0.000000 1 05.05.2025 14:36:06 0.000000 Pause 2.875 0 0 ...
0.001000 2 05.05.2025 14:36:07 0.001000 Charge 2.876 0.005 0 ...
```

### **Test Plan Files (Optional)**

Upload `.txt` test plan files for automatic C-rate detection:
```
Charge                I=0.1CA    U>3.9V
Discharge             I=0.1CA    U<1.5V  
Cycle-end             Count=3

Charge                I=0.2CA    U>3.9V
Discharge             I=0.2CA    U<1.5V
Cycle-end             Count=5
```

## 🔬 Analysis Features

### **Cycle Detection**
- **State-based** (Recommended): Uses the `State` column to identify cycle boundaries
- **Zero-crossing**: Detects boundaries based on current sign changes

### **Capacity Calculation**
- Trapezoidal integration of current over time
- Absolute capacity (Ah) and specific capacity (mAh/g)
- Separate analysis for charge and discharge cycles

### **Visualizations**
- Capacity vs cycle number trends
- Specific capacity evolution
- Voltage range analysis
- Cycle duration patterns

### **Export Options**
- **CSV files** with metadata and analysis parameters
- **Interactive plots** with zoom and export capabilities
- **Detailed logs** for troubleshooting

## 🆘 Troubleshooting

### **Python Installation Issues**

**"Python is not recognized"**
1. Install Python from [python.org](https://python.org)
2. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
3. Restart your computer
4. Verify: `python --version` should work

**Quick Python Install (Windows):**
```cmd
# Windows 10/11 with winget
winget install Python.Python.3

# Or with PowerShell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe" -OutFile "python-installer.exe"
Start-Process -FilePath "python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
```

### **Application Issues**

**Package errors**: Delete any `venv` folder and run the quick start script again

**Port in use**: Change port in launcher script (e.g., `--server.port 8502`)

**Browser doesn't open**: Manually go to `http://localhost:8501`

**Large file uploads**: May take time - be patient during processing

### **Advanced Options**

**Running from Command Line:**
```bash
# Navigate to the tool directory
cd battery_cycle_analyzer

# Install dependencies (one time)
pip install -r ../requirements.txt

# Start application
streamlit run src/gui.py
```

**Multiple Instances:** Edit launcher scripts to use different ports (8501, 8502, 8503, etc.)

## 💡 Launcher Comparison

| Script | Platform | Virtual Env | Auto-Install | Best For |
|--------|----------|-------------|--------------|----------|
| `quick_start.bat` | Windows | ✅ | ✅ | **End users** |
| `quick_start.py` | All | ✅ | ✅ | **Cross-platform** |
| `setup_windows.bat` | Windows | ❌ | ✅ | **One-time setup** |
| `run_battery_analyzer.bat` | Windows | ❌ | ✅ | **Fallback option** |
| `launch.py` | All | ❌ | ✅ | **Legacy support** |

**Recommendation**: Start with `quick_start.bat` (Windows) or `quick_start.py` (Mac/Linux). These create isolated virtual environments and have the best error handling.

## 🔧 For Developers

### **Project Structure**
```
battery_analysis/                # Root directory
├── requirements.txt            # Shared dependencies
├── battery_cycle_analyzer/     # This tool
│   ├── quick_start.bat         # Main Windows launcher
│   ├── quick_start.py          # Main cross-platform launcher
│   ├── src/
│   │   ├── gui.py             # Streamlit web interface
│   │   └── analyzer.py        # Core analysis engine
│   ├── deployment/            # Alternative launchers
│   └── tests/                 # Test scripts
└── [future_tools]/            # Other battery analysis tools
```

### **Dependencies**
- `streamlit>=1.28.0` - Web application framework
- `pandas>=1.5.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.10.0` - Scientific computing (integration)
- `plotly>=5.15.0` - Interactive visualizations
- `matplotlib>=3.6.0` - Additional plotting

### **Virtual Environment Benefits**
- ✅ No conflicts with other Python projects
- ✅ Clean, isolated package installation
- ✅ Reproducible environment
- ✅ Safe system Python management

---

## 📚 Additional Resources

**For detailed launcher information**: See `LAUNCHER_GUIDE.md`

**For file format questions**: Upload a sample file - the tool provides helpful error messages

**For development**: Check the `tests/` directory for example scripts

---

*This tool is provided for research and educational purposes.* 