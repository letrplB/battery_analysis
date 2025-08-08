# Setup Guide - Battery Cycle Analyzer

This guide will help you set up the Battery Cycle Analyzer after cloning the battery_analysis repository from GitHub.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads/)
- **pip** - Usually comes with Python installation

### Verify Prerequisites

Open a terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
# Check Python version
python --version
# or
python3 --version

# Check pip
pip --version
# or
pip3 --version

# Check git
git --version
```

## Step 1: Clone the Repository

```bash
# Clone the main battery_analysis repository
git clone https://github.com/letrplB/battery_analysis.git

# Navigate to the repository root
cd battery_analysis
```

## Step 2: Set Up Python Environment

The repository uses a shared virtual environment at the root level for all packages.

### Option A: Using venv (Recommended)

#### Windows
```cmd
# Create virtual environment at repository root
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

#### Mac/Linux
```bash
# Create virtual environment at repository root
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

### Option B: Using conda (Alternative)

```bash
# Create conda environment
conda create -n battery_analysis python=3.9

# Activate environment
conda activate battery_analysis
```

## Step 3: Install Dependencies

The repository uses a shared `requirements.txt` at the root level:

```bash
# Make sure you're in the repository root
cd battery_analysis

# With virtual environment activated, install dependencies
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist at the root, install manually:

```bash
pip install streamlit pandas numpy scipy plotly openpyxl xlsxwriter chardet
```

### Common Installation Issues

**"pip: command not found"**
- Try `pip3` instead of `pip`
- Or use: `python -m pip install ...`

**Permission errors on Mac/Linux**
- Never use `sudo pip install`
- Make sure your virtual environment is activated

**SSL Certificate errors**
```bash
# Temporary workaround (use with caution)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package_name>
```

## Step 4: Verify Installation

Test that all dependencies are installed correctly:

```bash
# Check Streamlit
python -c "import streamlit; print('Streamlit OK')"

# Check all dependencies
python -c "
import streamlit
import pandas
import numpy
import scipy
import plotly
print('All dependencies OK')
"
```

## Step 5: Run the Battery Cycle Analyzer

```bash
# Navigate to the battery_cycle_analyzer package
cd battery_cycle_analyzer

# Run the application
streamlit run src/gui_modular.py
```

The application should:
1. Start the Streamlit server
2. Open your default browser automatically
3. Display the Battery Cycle Analyzer interface

If the browser doesn't open automatically, navigate to:
- http://localhost:8501

## Step 6: First Run Checklist

Once the application is running:

1. **Test with sample data**:
   - Click on "Data Input" in the sidebar
   - Select "Basytec" as device type
   - Upload a sample `.txt` file

2. **Configure parameters**:
   - Set Active Material Weight (e.g., 0.035 g)
   - Set Theoretical Capacity (e.g., 0.050 Ah)

3. **Run analysis**:
   - Click "Prepare Data"
   - Select "Standard Cycle" analysis
   - Click "Run Standard Analysis"

## Repository Structure Overview

```
battery_analysis/              # Root repository
├── venv/                     # Shared virtual environment
├── requirements.txt          # Shared dependencies
├── README.md                 # Repository documentation
├── battery_cycle_analyzer/   # Battery Cycle Analyzer package
│   ├── src/                 # Source code
│   │   ├── gui_modular.py  # Main application
│   │   ├── core/           # Core modules
│   │   ├── analysis_modes/ # Analysis algorithms
│   │   └── gui_components/ # UI components
│   ├── data/               # Data directory
│   │   └── output/        # Export location
│   ├── logs/              # Application logs
│   ├── .streamlit/        # Streamlit config
│   ├── README.md          # Package documentation
│   ├── SETUP.md           # This file
│   └── requirements.txt   # Package-specific deps (if any)
├── [future_package]/        # Future analysis tools
└── .gitignore              # Git ignore rules
```

## Working with Multiple Packages

The `battery_analysis` repository is designed to host multiple battery analysis tools:

1. **Shared Environment**: All packages use the root `venv/` and `requirements.txt`
2. **Independent Packages**: Each package (like `battery_cycle_analyzer`) can run independently
3. **Future Packages**: New analysis tools can be added as separate directories

### Running Different Packages

```bash
# Always start from repository root
cd battery_analysis

# Activate the shared virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Navigate to desired package
cd battery_cycle_analyzer
streamlit run src/gui_modular.py

# Or for future packages
cd other_analyzer
python main.py
```

## Troubleshooting

### Application won't start

**"streamlit: command not found"**
- Make sure you activated the virtual environment from the repository root
- Reinstall: `pip install streamlit`

**Port already in use**
```bash
# Use a different port
streamlit run src/gui_modular.py --server.port 8502
```

**Module import errors**
```bash
# Go back to repository root
cd ..
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

### Data processing issues

**File upload fails**
- Check file format (should be .txt or .csv)
- Ensure file size is under 200MB (Streamlit default)

**"No cycles detected"**
- Verify your data has State column (for state-based detection)
- Try zero-crossing detection method instead

### Performance issues

**Slow processing**
- Large files (>100MB) will take time
- Consider splitting very large datasets
- Close other applications to free memory

## Development Setup

For development and contributions:

### Install development dependencies
```bash
# From repository root with venv activated
pip install pytest black flake8 mypy
```

### Run code formatting
```bash
# Format battery_cycle_analyzer package
black battery_cycle_analyzer/src/
```

### Run linting
```bash
flake8 battery_cycle_analyzer/src/
```

### Run type checking
```bash
mypy battery_cycle_analyzer/src/
```

## Getting Help

1. **Check the documentation**:
   - Repository README.md for overall structure
   - battery_cycle_analyzer/README.md for package usage
   - battery_cycle_analyzer/src/README.md for technical details

2. **Check logs**:
   - Look in `battery_cycle_analyzer/logs/` for error details

3. **Common issues**:
   - Most issues are dependency-related
   - Make sure you're using the shared venv from root

4. **Report issues**:
   - GitHub: https://github.com/letrplB/battery_analysis/issues
   - Include Python version
   - Include error messages from logs
   - Include sample data if possible

## Next Steps

After successful setup:

1. **Read the package README** (`battery_cycle_analyzer/README.md`) for detailed usage
2. **Try different analysis modes**:
   - Standard Cycle Analysis
   - dQ/dU Analysis
   - Combined Analysis
3. **Explore export options**:
   - CSV for data analysis
   - Excel for reports
   - JSON for programmatic access

## Quick Commands Reference

```bash
# From repository root
cd battery_analysis

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install/update dependencies
pip install -r requirements.txt

# Navigate to battery_cycle_analyzer
cd battery_cycle_analyzer

# Run application
streamlit run src/gui_modular.py

# Deactivate virtual environment
deactivate

# Update dependencies
pip install --upgrade -r ../requirements.txt

# Clean up (from repository root)
rm -rf venv/             # Remove virtual environment
pip cache purge          # Clear pip cache
```

## Contributing

Before contributing:
1. Fork the repository at https://github.com/letrplB/battery_analysis
2. Create a feature branch
3. Follow the code style guidelines
4. Test your changes in the shared environment
5. Submit a pull request

### Adding New Packages

To add a new analysis package to the repository:
1. Create a new directory at the repository root
2. Follow the structure of `battery_cycle_analyzer`
3. Use the shared virtual environment and requirements
4. Document in the main repository README

---

**Need help?** Create an issue on GitHub with:
- Your operating system
- Python version
- Which package you're trying to run
- Error messages
- Steps to reproduce the problem