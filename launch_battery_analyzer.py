#!/usr/bin/env python3
"""
Cross-platform launcher for Battery Cycle Analyzer
Handles venv setup, dependency installation, and application launch
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# ANSI color codes for terminal output (cross-platform)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Print application header"""
    print("=" * 50)
    print(f"{Colors.CYAN}{Colors.BOLD}   Battery Cycle Analyzer Launcher{Colors.RESET}")
    print("=" * 50)
    print()

def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def check_python():
    """Check if Python is installed and version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8 or higher is required. Found: {version.major}.{version.minor}")
        return False
    print_success(f"Found Python {version.major}.{version.minor}.{version.micro}")
    return True

def get_venv_path():
    """Get the virtual environment path"""
    return Path.cwd() / "venv"

def get_venv_python():
    """Get the Python executable in the virtual environment"""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_venv_pip():
    """Get the pip executable in the virtual environment"""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def create_venv():
    """Create virtual environment"""
    print_info("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to create virtual environment")
        return False

def install_dependencies():
    """Install required dependencies"""
    print_info("Installing dependencies...")
    print("This may take a few minutes on first run...")
    
    venv_pip = get_venv_pip()
    venv_python = get_venv_python()
    
    # Upgrade pip first
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print_success("Pip upgraded")
    except subprocess.CalledProcessError:
        print_warning("Could not upgrade pip")
    
    # Install from requirements.txt if it exists
    requirements_file = Path.cwd() / "requirements.txt"
    if requirements_file.exists():
        print_info("Installing from requirements.txt...")
        try:
            subprocess.run([str(venv_pip), "install", "-r", "requirements.txt"], 
                          check=True)
            print_success("Dependencies installed from requirements.txt")
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to install from requirements.txt")
            return False
    else:
        # Install packages manually
        print_info("Installing packages manually...")
        packages = [
            "streamlit",
            "pandas",
            "numpy",
            "scipy",
            "plotly",
            "openpyxl",
            "xlsxwriter",
            "chardet"
        ]
        
        for package in packages:
            try:
                print(f"  Installing {package}...")
                subprocess.run([str(venv_pip), "install", package], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print_error(f"Failed to install {package}")
                return False
        
        print_success("All dependencies installed")
        return True

def run_application():
    """Run the Streamlit application"""
    # Navigate to battery_cycle_analyzer
    app_dir = Path.cwd() / "battery_cycle_analyzer"
    if not app_dir.exists():
        print_error("Cannot find battery_cycle_analyzer directory")
        return False
    
    app_file = app_dir / "src" / "gui_modular.py"
    if not app_file.exists():
        print_error(f"Cannot find {app_file}")
        return False
    
    os.chdir(app_dir)
    
    print()
    print_success("Starting Battery Cycle Analyzer...")
    print()
    print("The application will open in your default browser.")
    print("If it doesn't open automatically, navigate to: http://localhost:8501")
    print()
    print("=" * 50)
    print(f"{Colors.YELLOW}Press Ctrl+C to stop the application{Colors.RESET}")
    print("=" * 50)
    print()
    
    venv_python = get_venv_python()
    
    try:
        # Run Streamlit
        subprocess.run([str(venv_python), "-m", "streamlit", "run", "src/gui_modular.py"])
    except KeyboardInterrupt:
        print()
        print_info("Shutting down application...")
    except Exception as e:
        print_error(f"Error running application: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print_header()
    
    # Check Python version
    if not check_python():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print()
    
    # Check if venv exists
    venv_path = get_venv_path()
    venv_python = get_venv_python()
    
    if venv_path.exists() and venv_python.exists():
        print_success("Virtual environment found")
    else:
        print_info("No virtual environment found")
        if not create_venv():
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        print()
        if not install_dependencies():
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        print()
        print("=" * 50)
        print(f"{Colors.GREEN}{Colors.BOLD}   Installation complete!{Colors.RESET}")
        print("=" * 50)
    
    # Run the application
    if not run_application():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print(f"{Colors.CYAN}   Application stopped{Colors.RESET}")
    print("=" * 50)
    
    # Keep terminal open on Windows
    if platform.system() == "Windows":
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()