#!/bin/bash

# Battery Cycle Analyzer Launcher for Mac/Linux
# This script handles venv setup, dependency installation, and app launch

echo "========================================="
echo "   Battery Cycle Analyzer Launcher"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo -e "${RED}ERROR: Python is not installed${NC}"
    echo ""
    echo "Please install Python 3.8 or higher from https://python.org"
    echo "Or use your package manager:"
    echo "  Mac: brew install python3"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Virtual environment found."
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found."
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo ""
    echo "Installing dependencies..."
    echo "This may take a few minutes on first run..."
    
    # Upgrade pip first
    python -m pip install --upgrade pip
    
    # Install from requirements.txt if it exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install manually if requirements.txt doesn't exist
        pip install streamlit pandas numpy scipy plotly openpyxl xlsxwriter chardet
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install dependencies${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    echo ""
    echo "========================================="
    echo "   Installation complete!"
    echo "========================================="
fi

# Navigate to battery_cycle_analyzer
cd battery_cycle_analyzer

# Check if the package directory exists
if [ ! -f "src/gui_modular.py" ]; then
    echo -e "${RED}ERROR: Cannot find battery_cycle_analyzer/src/gui_modular.py${NC}"
    echo "Please make sure you're running this from the battery_analysis root directory"
    read -p "Press Enter to exit..."
    exit 1
fi

# Function to handle shutdown
shutdown_app() {
    echo ""
    echo "========================================="
    echo "   Shutting down application..."
    echo "========================================="
    exit 0
}

# Set up signal handler for Ctrl+C
trap shutdown_app INT

# Start the application
echo ""
echo -e "${GREEN}Starting Battery Cycle Analyzer...${NC}"
echo ""
echo "The application will open in your default browser."
echo "If it doesn't open automatically, navigate to: http://localhost:8501"
echo ""
echo "========================================="
echo "   Press Ctrl+C to stop the application"
echo "========================================="
echo ""

# Run Streamlit
streamlit run src/gui_modular.py

# When user stops the app
echo ""
echo "========================================="
echo "   Application stopped"
echo "========================================="
echo ""
read -p "Press Enter to exit..."