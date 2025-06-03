# 🔋 Battery Cycle Analyzer

A Python-based tool for analyzing battery cycle stability data from Basytec Battery Test System files.

## 🚀 Quick Start

### **Easiest Method (Recommended)**

1. **Windows**: Double-click `battery_cycle_analyzer/quick_start.bat`
2. **Mac/Linux**: Run `python3 battery_cycle_analyzer/quick_start.py`

That's it! The application will:
- ✅ Create a virtual environment automatically
- ✅ Install all dependencies 
- ✅ Open in your web browser at http://localhost:8501

### **Alternative Methods**

- **Windows Setup**: Run `battery_cycle_analyzer/deployment/windows/setup_windows.bat` for one-time setup
- **Cross-Platform**: Use `battery_cycle_analyzer/deployment/cross_platform/launch.py`
- **PowerShell**: Run `battery_cycle_analyzer/deployment/windows/run_battery_analyzer.ps1`

## 📋 Requirements

- Python 3.8 or higher
- Internet connection (for first-time setup only)

## 📁 Project Structure

```
battery_analysis/                # Root directory for battery tools
├── requirements.txt            # ⭐ Shared dependencies for all tools
├── battery_cycle_analyzer/     # Battery cycle analysis tool
│   ├── quick_start.bat         # ⭐ Main Windows launcher
│   ├── quick_start.py          # ⭐ Main cross-platform launcher
│   ├── src/
│   │   ├── gui.py             # Web interface
│   │   └── analyzer.py        # Analysis engine
│   ├── deployment/            # Alternative launchers
│   └── docs/                  # Documentation
└── future_tool_2/             # Placeholder for additional tools
```

## 📖 Usage

1. Start the application using one of the quick start methods above
2. Upload your Basytec data file (.txt or .csv)
3. Set analysis parameters (weight, C-rates, etc.)
4. Click "Analyze Data"
5. View results and download CSV

## 📚 Documentation

- `battery_cycle_analyzer/LAUNCHER_GUIDE.md` - Detailed guide to all launcher options
- `battery_cycle_analyzer/docs/README.md` - Full documentation
- `battery_cycle_analyzer/docs/README_WINDOWS.md` - Windows-specific instructions

## 🆘 Troubleshooting

If you encounter issues:

1. **Python not found**: Install Python from [python.org](https://python.org) and make sure to check "Add to PATH"
2. **Package errors**: Delete any `venv` folder and run the quick start script again
3. **Port in use**: Close other instances or change the port in the launcher script

For more help, see the documentation in the `battery_cycle_analyzer/docs/` folder.

## Features

- 📁 **File Parsing**: Automatic parsing of Basytec data files with metadata extraction
- 🔍 **Cycle Detection**: Multiple methods for detecting charge/discharge cycle boundaries
- 📊 **Capacity Analysis**: Calculation of capacity (Ah) and specific capacity (mAh/g) per cycle
- 📈 **Visualizations**: Interactive plots showing capacity trends, voltage ranges, and cycle duration
- 💾 **Export Results**: Download analysis results as CSV files with metadata
- 🌐 **Web Interface**: User-friendly Streamlit-based GUI that runs in your browser

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd battery-cycle-analyzer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

1. **Activate your virtual environment** (if not already active)
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Run the Streamlit application**
   ```bash
   streamlit run gui.py
   ```

3. **Open your browser** to the displayed URL (typically `http://localhost:8501`)

### Using the Interface

1. **Upload Data File**: Click "Browse files" and select your Basytec .txt or .csv file
2. **Set Parameters**:
   - Enter the active material weight in grams
   - Choose boundary detection method (State-based recommended)
3. **Analyze**: Click "Analyze Data" to process your file
4. **Review Results**: Examine the summary statistics, cycle data table, and visualizations
5. **Download**: Save results as CSV for further analysis

## File Format

The tool expects Basytec Battery Test System files with:

- **Metadata headers** starting with `~`
- **Space or tab-separated** data columns
- **Required columns**:
  - `Time[h]` - elapsed time in hours
  - `Command` - operation type (charge, discharge, pause)
  - `U[V]` - voltage in volts
  - `I[A]` - current in amperes
  - `State` - cycle state indicator

### Example File Structure

```
~Resultfile from Basytec Battery Test System
~Date and Time of Data Converting: 19.05.2025 14:36:50
~Name of Test: KM_KMFO_721_F1_E5 50mAhg 2xF 05052025
~Battery: KM-KMFO-721-F1E5(16) 50mAh 2xF
~Start of Test: 05.05.2025 16:35:43
~End of Test: 15.05.2025 13:43:08
~
~Time[h] DataSet DateTime t-Step[h] t-Set[h] t-Cyc[h] Line Command U[V] I[A] Ah[Ah] ...
0.000000 1 05.05.2025 14:36:06 0.000000 0.000000 0.000000 2 Pause 2.875 0 0 ...
```

## Analysis Methods

### Boundary Detection

- **State-based** (Recommended): Uses the `State` column to identify cycle boundaries
- **Zero-crossing**: Detects boundaries based on current sign changes

### Capacity Calculation

- Uses trapezoidal integration of current over time
- Calculates both absolute capacity (Ah) and specific capacity (mAh/g)
- Focuses on discharge cycles for capacity analysis

## Output

The analysis provides:

- **Summary Statistics**: Total cycles, capacity retention, average values
- **Cycle Data Table**: Detailed results for each cycle
- **Visualizations**: 
  - Capacity vs cycle number
  - Specific capacity trends
  - Voltage range evolution
  - Cycle duration analysis
- **CSV Export**: Complete results with metadata for further analysis

## Project Structure

```
battery-cycle-analyzer/
├── analyzer.py          # Core analysis functions
├── gui.py              # Streamlit web interface
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── import_data/       # Directory for input data files
```

## Dependencies

- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `scipy` - Scientific computing (integration)
- `streamlit` - Web application framework
- `plotly` - Interactive visualizations
- `matplotlib` - Additional plotting capabilities

## Troubleshooting

### Common Issues

1. **File parsing errors**: Ensure your file follows the expected Basytec format
2. **No cycles found**: Try different boundary detection methods
3. **Memory issues**: For very large files, consider data preprocessing
4. **Import errors**: Ensure all dependencies are installed in your virtual environment

### Getting Help

If you encounter issues:

1. Check that your data file matches the expected format
2. Verify all dependencies are installed correctly
3. Try both boundary detection methods
4. Check the error messages in the application for specific guidance

## Future Enhancements

- Support for charge cycle analysis
- Differential capacity (dQ/dV) analysis
- Advanced filtering and preprocessing options
- Batch processing capabilities
- Export to additional formats (Excel, PowerPoint)

## License

This project is provided as-is for research and educational purposes. 