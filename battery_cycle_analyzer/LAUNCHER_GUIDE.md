# Battery Cycle Analyzer - Launcher Guide

This project includes several launcher scripts for different purposes and platforms. Here's when to use each one:

## 🐍 Prerequisites: Installing Python

**IMPORTANT**: You need Python installed before any launcher will work!

### **🖥️ Windows - Install Python via Terminal**

Open **Command Prompt** or **PowerShell** as **Administrator** and run one of these commands:

#### **Method 1: winget (Recommended - Windows 10/11)**
```cmd
winget install Python.Python.3.11
```
Or for the latest version:
```cmd
winget install Python.Python.3
```

#### **Method 2: Chocolatey (If you have Chocolatey)**
```cmd
choco install python
```

#### **Method 3: Scoop (If you have Scoop)**
```cmd
scoop install python
```

#### **Method 4: PowerShell Direct Download**
```powershell
# Download and install Python 3.11 automatically
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe" -OutFile "python-installer.exe"
Start-Process -FilePath "python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Remove-Item "python-installer.exe"
```

### **🍎 Mac - Install Python**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
# Python 3 may already be installed - check with:
python3 --version
```

### **🐧 Linux - Install Python**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL/Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

### **✅ Verify Installation**
After installation, verify Python is working:
```cmd
python --version
pip --version
```

**Both commands should return version numbers.** If they don't:
1. **Restart your terminal/computer**
2. **Make sure Python was added to PATH during installation**
3. **Try using `python3` instead of `python`**

---

## 🚀 Main Entry Points (Use These!)

### `quick_start.bat` (Windows - RECOMMENDED)
**Purpose**: Complete setup and launch for Windows users
- ✅ **Creates virtual environment** automatically
- ✅ **Auto-installs all dependencies** from requirements.txt
- ✅ **Most robust error handling** and troubleshooting
- ✅ **One-click solution** - just double-click to start
- ✅ **Browser auto-opens** to the application
- ✅ **Persistent setup** - runs faster on subsequent launches

**When to use**: This should be your first choice on Windows. Perfect for end users.

### `quick_start.py` (Cross-Platform - RECOMMENDED)
**Purpose**: Complete setup and launch for all operating systems
- ✅ **Creates virtual environment** automatically (Windows/Mac/Linux)
- ✅ **Auto-installs all dependencies** from requirements.txt
- ✅ **Cross-platform compatibility**
- ✅ **Robust error handling** with detailed feedback
- ✅ **Smart Python executable detection**

**When to use**: Use this on Mac, Linux, or if you prefer Python scripts on Windows.

---

## 🛠️ Setup and Deployment Scripts

### `deployment/windows/setup_windows.bat`
**Purpose**: One-time complete setup for Windows
- ✅ **Full system setup** with all dependencies
- ✅ **Creates desktop shortcut**
- ✅ **Tests the installation**
- ✅ **Configures the environment**

**When to use**: Run this once for initial setup, then use `quick_start.bat` daily.

### `deployment/windows/run_battery_analyzer.bat`
**Purpose**: Basic Windows launcher (legacy)
- ⚠️ **No virtual environment** (uses system Python)
- ✅ **Installs dependencies** but less robust
- ⚠️ **Minimal error handling**

**When to use**: Fallback option if `quick_start.bat` doesn't work.

### `deployment/windows/run_battery_analyzer.ps1`
**Purpose**: PowerShell launcher for Windows
- ⚠️ **No virtual environment** (uses system Python)
- ✅ **Good package management**
- ✅ **Nice colored output**

**When to use**: If you prefer PowerShell or have batch file restrictions.

### `deployment/cross_platform/launch.py`
**Purpose**: Basic cross-platform launcher (legacy)
- ⚠️ **No virtual environment** (uses system Python)
- ✅ **Cross-platform support**
- ⚠️ **Less robust than quick_start.py**

**When to use**: Fallback for cross-platform use if `quick_start.py` doesn't work.

---

## 📋 Quick Reference

| Script | Platform | Virtual Env | Auto-Install | Recommended |
|--------|----------|-------------|--------------|-------------|
| `quick_start.bat` | Windows | ✅ | ✅ | ⭐ **BEST** |
| `quick_start.py` | All | ✅ | ✅ | ⭐ **BEST** |
| `setup_windows.bat` | Windows | ❌ | ✅ | Setup only |
| `run_battery_analyzer.bat` | Windows | ❌ | ✅ | Fallback |
| `run_battery_analyzer.ps1` | Windows | ❌ | ✅ | Fallback |
| `launch.py` | All | ❌ | ✅ | Fallback |

---

## 🔧 What's the Big Difference?

### **Virtual Environment Support**
The main difference is that `quick_start.bat` and `quick_start.py` create isolated Python environments:

**With Virtual Environment** (quick_start scripts):
- ✅ **No conflicts** with other Python projects
- ✅ **Clean, isolated** package installation
- ✅ **Reproducible** - same environment every time
- ✅ **Safe** - won't mess up your system Python

**Without Virtual Environment** (other scripts):
- ⚠️ **System-wide** package installation
- ⚠️ **Potential conflicts** with other Python projects
- ⚠️ **Less predictable** behavior

### **Error Handling & User Experience**
The quick_start scripts have much better:
- 🔍 **Detailed error messages** with solutions
- 📋 **Step-by-step progress** feedback
- 🛠️ **Automatic troubleshooting** attempts
- 💡 **Clear instructions** when things go wrong

---

## 💡 Recommendations

1. **Install Python first** using the commands above
2. **First time setup**: Use `quick_start.bat` (Windows) or `quick_start.py` (other platforms)
3. **Daily use**: Just double-click the same script - it remembers your setup
4. **Problems?**: Try `deployment/windows/setup_windows.bat` for a fresh start
5. **Advanced users**: You can still use the other scripts if needed

---

## 🆘 Troubleshooting

### **"Python is not installed or not found in PATH!"**
1. **Install Python** using the commands in the Prerequisites section above
2. **Restart your terminal/computer** after installation
3. **Verify installation**: Run `python --version` in a new terminal
4. **Check PATH**: Make sure Python was added to PATH during installation

### **Other Issues**
If `quick_start.bat` or `quick_start.py` don't work:

1. **Try running as administrator** (Windows)
2. **Check Python installation**: `python --version`
3. **Update pip**: `python -m pip install --upgrade pip`
4. **Manual install**: `pip install -r ../requirements.txt`
5. **Use fallback scripts** in the deployment folder
6. **Delete `venv` folder** and try again for a fresh start

### **Platform-Specific Notes**
- **Windows**: Use `python` command
- **Mac/Linux**: May need to use `python3` command instead
- **Permission issues**: Try running as administrator/sudo
- **Corporate networks**: May need proxy configuration for pip 