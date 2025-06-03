#!/usr/bin/env python3
"""
Battery Cycle Analyzer - Universal Launcher
This script automatically installs dependencies and starts the Streamlit application.
"""

import sys
import subprocess
import importlib
import webbrowser
import time
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or newer is required.")
        print(f"   Current version: Python {sys.version}")
        print("   Please upgrade Python from https://python.org")
        input("Press Enter to exit...")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_package(package_name, import_name=None):
    """Install a package using pip."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"  ✅ {package_name}")
        return True
    except ImportError:
        print(f"  📦 Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"  ✅ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed to install {package_name}")
            return False

def install_requirements():
    """Install all required packages from root-level requirements.txt."""
    print("🔍 Checking required packages...")
    
    # Get the project root directory (two levels up from deployment/cross_platform/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if requirements_file.exists():
        print(f"📦 Installing packages from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            print("✅ All packages from requirements.txt installed!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install from requirements.txt, trying individual packages...")
    
    # Fallback to individual package installation
    packages = [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("plotly", "plotly"),
        ("matplotlib", "matplotlib")
    ]
    
    failed_packages = []
    
    for package_name, import_name in packages:
        if not install_package(package_name, import_name):
            failed_packages.append(package_name)
    
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("Please install them manually using:")
        print(f"pip install {' '.join(failed_packages)}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("✅ All packages are installed!")
    return True

def start_streamlit():
    """Start the Streamlit application."""
    print("\n🚀 Starting Battery Cycle Analyzer...")
    print("📝 The application will open in your web browser")
    print("🔴 To stop the application, close this window or press Ctrl+C")
    print("=" * 50)
    
    # Get the project root directory (two levels up from deployment/cross_platform/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    gui_file = project_root / "src" / "gui.py"
    
    if not gui_file.exists():
        print("❌ Error: gui.py not found!")
        print(f"   Looking for: {gui_file}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Change to src directory
    src_dir = project_root / "src"
    os.chdir(src_dir)
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "gui.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to exit...")

def main():
    """Main launcher function."""
    print("🔋 Battery Cycle Analyzer")
    print("=" * 30)
    
    # Check Python version
    check_python_version()
    
    # Install packages
    install_requirements()
    
    # Start application
    start_streamlit()

if __name__ == "__main__":
    main() 