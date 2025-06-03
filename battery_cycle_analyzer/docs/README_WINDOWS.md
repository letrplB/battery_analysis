# 🔋 Battery Cycle Analyzer - Windows Installation Guide

## 📥 Quick Start (Easiest Method)

### **Option 1: Automatic Setup (Recommended)**
1. **Download** this folder to your computer
2. **Double-click** `setup_windows.bat`
3. **Follow the prompts** - the script will install everything automatically
4. **Done!** A desktop shortcut will be created

### **Option 2: Manual Double-Click**
1. **Double-click** `run_battery_analyzer.bat`
2. **Wait** for the application to start (may take 30 seconds first time)
3. **Your browser** will open automatically with the application

---

## 🛠️ Prerequisites

### **Python Installation**
- **Download Python** from [python.org](https://www.python.org/downloads/)
- **IMPORTANT**: Check "Add Python to PATH" during installation
- **Minimum version**: Python 3.8 or newer

### **Internet Connection**
- Required for first-time package installation only
- After setup, the application works offline

---

## 🚀 How to Use

### **Starting the Application**
1. **Double-click** the desktop shortcut "Battery Cycle Analyzer"
   - OR double-click `run_battery_analyzer.bat` in the application folder
2. **Wait** for your web browser to open (usually takes 10-30 seconds)
3. **The application** will appear at `http://localhost:8501`

### **Using the Application**
1. **Upload your Basytec data file** (.txt or .csv)
2. **Set parameters**:
   - Active material weight (grams)
   - Theoretical capacity (Ah)
   - C-rate configurations
3. **Click "Analyze"** to process your data
4. **Download results** and view interactive plots

### **Stopping the Application**
- **Close the black terminal window** that opened with the application
- OR press **Ctrl+C** in the terminal window

---

## 📁 Files Included

| File | Purpose |
|------|---------|
| `setup_windows.bat` | One-time installation script |
| `run_battery_analyzer.bat` | Main application launcher |
| `run_battery_analyzer.ps1` | PowerShell alternative launcher |
| `gui.py` | Web-based user interface |
| `analyzer.py` | Core analysis engine |
| `requirements.txt` | Python package dependencies |

---

## ❓ Troubleshooting

### **"Python is not recognized"**
- **Solution**: Install Python from [python.org](https://www.python.org/downloads/)
- **Make sure** to check "Add Python to PATH" during installation
- **Restart** your computer after installation

### **"Module not found" errors**
- **Solution**: Run `setup_windows.bat` to install required packages
- **Or manually run**: `pip install -r requirements.txt`

### **Browser doesn't open automatically**
- **Manual**: Open your browser and go to `http://localhost:8501`
- **Check**: Make sure no firewall is blocking the application

### **Application won't start**
- **Check**: Python is installed and in PATH
- **Run**: `setup_windows.bat` to reinstall packages
- **Try**: Running `run_battery_analyzer.ps1` instead

### **Port already in use**
- **Close** any other instances of the application
- **Or change** the port in the batch file (e.g., `--server.port 8502`)

---

## 🔧 Advanced Options

### **Running from Command Line**
```bash
# Navigate to the application folder
cd path\to\battery_analyzer

# Install dependencies (one time only)
pip install -r requirements.txt

# Start the application
streamlit run gui.py
```

### **Custom Port**
Edit `run_battery_analyzer.bat` and change `8501` to your preferred port:
```batch
python -m streamlit run gui.py --server.port 8502 --server.headless true
```

### **Multiple Instances**
- Use different ports for each instance
- Edit the batch file to use ports 8501, 8502, 8503, etc.

---

## 📞 Support

### **Common Issues**
1. **Slow first startup**: Normal - packages are being loaded
2. **Browser security warnings**: Click "Advanced" → "Proceed" (localhost is safe)
3. **Large file uploads**: May take time depending on file size

### **Getting Help**
- Check this README first
- Ensure Python and packages are properly installed
- Try the PowerShell version if batch file fails

---

## 🎯 Features

- ✅ **Drag & drop** file upload
- ✅ **Interactive plots** with zoom and export
- ✅ **Automatic C-rate detection** from test plans
- ✅ **CSV export** of results
- ✅ **Real-time progress** indicators
- ✅ **Comprehensive error checking**
- ✅ **Works offline** after initial setup

---

*Last updated: December 2024* 