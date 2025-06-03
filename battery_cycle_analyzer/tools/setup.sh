#!/bin/bash

# Battery Cycle Analyzer Setup Script
# This script sets up the virtual environment and installs dependencies

echo "🔋 Battery Cycle Analyzer Setup"
echo "================================"

# Change to project root (one level up from tools)
cd "$(dirname "$0")/.."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r config/requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Run: python3 quick_start.py (recommended), OR"
echo "2. Manually:"
echo "   - Activate the virtual environment: source venv/bin/activate"
echo "   - Change to src directory: cd src"
echo "   - Run the application: streamlit run gui.py"
echo "   - Open your browser to the displayed URL (typically http://localhost:8501)"
echo ""
echo "To deactivate the virtual environment later, run: deactivate" 