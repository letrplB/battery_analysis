#!/usr/bin/env python3
"""
Battery Cycle Analyzer - Cross-Platform Quick Start
This script automatically creates a virtual environment, installs dependencies, and starts the application.
"""

import sys
import subprocess
import os
import platform
import venv
import webbrowser
import time
from pathlib import Path

def print_header():
    """Print the application header."""
    print("🔋 Battery Cycle Analyzer - Quick Start")
    print("=" * 50)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or newer is required.")
        print(f"   Current version: Python {sys.version}")
        print("   Please upgrade Python from https://python.org")
        input("Press Enter to exit...")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent

def get_venv_path():
    """Get the virtual environment path."""
    project_root = get_project_root()
    return project_root / "venv"

def get_python_executable():
    """Get the Python executable path for the virtual environment."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_pip_executable():
    """Get the pip executable path for the virtual environment."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = get_venv_path()
    
    if venv_path.exists():
        print("📦 Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def upgrade_pip():
    """Upgrade pip in the virtual environment."""
    print("⬆️ Upgrading pip...")
    python_exe = get_python_executable()
    
    try:
        subprocess.check_call([
            str(python_exe), "-m", "pip", "install", "--upgrade", "pip"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Pip upgraded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Warning: Could not upgrade pip: {e}")
        return True  # Continue anyway

def install_requirements():
    """Install required packages from requirements.txt."""
    print("📥 Installing/updating required packages...")
    project_root = get_project_root()
    requirements_file = project_root.parent / "requirements.txt"
    python_exe = get_python_executable()
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    try:
        subprocess.check_call([
            str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ All packages installed/updated successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        print("Please check your internet connection and try again.")
        return False

def check_gui_file():
    """Check if the GUI file exists."""
    project_root = get_project_root()
    gui_file = project_root / "src" / "gui.py"
    
    if not gui_file.exists():
        print(f"❌ GUI file not found: {gui_file}")
        print("Please ensure the project structure is complete.")
        return False
    
    return True

def start_streamlit():
    """Start the Streamlit application."""
    print("\n🚀 Starting Battery Cycle Analyzer...")
    print("📝 The application will open in your web browser")
    print("🔴 To stop the application, close this window or press Ctrl+C")
    print("=" * 50)
    print()
    
    project_root = get_project_root()
    python_exe = get_python_executable()
    
    # Change to src directory
    src_dir = project_root / "src"
    
    # Open browser after a delay
    def open_browser():
        time.sleep(5)
        webbrowser.open('http://localhost:8501')
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        # Start Streamlit
        subprocess.run([
            str(python_exe), "-m", "streamlit", "run", "gui.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], cwd=src_dir)
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to exit...")

def main():
    """Main function."""
    print_header()
    
    # Check Python version
    check_python_version()
    
    # Create virtual environment
    if not create_virtual_environment():
        input("Press Enter to exit...")
        return
    
    # Upgrade pip
    upgrade_pip()
    
    # Install requirements
    if not install_requirements():
        input("Press Enter to exit...")
        return
    
    # Check GUI file exists
    if not check_gui_file():
        input("Press Enter to exit...")
        return
    
    # Start application
    start_streamlit()

if __name__ == "__main__":
    main() 