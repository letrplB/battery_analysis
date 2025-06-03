# Battery Cycle Analyzer - PowerShell Launcher
# This script starts the Streamlit-based Battery Cycle Analyzer

Write-Host "🔋 Battery Cycle Analyzer" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting application..." -ForegroundColor Yellow
Write-Host "Your web browser will open automatically when ready." -ForegroundColor Cyan
Write-Host ""

# Change to project root (two levels up from script directory)
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install/update packages from requirements.txt
Write-Host "📦 Installing/updating packages from requirements.txt..." -ForegroundColor Yellow

try {
    pip install -r config\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Package installation failed"
    }
    Write-Host "✅ All packages installed/updated successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Some packages may have failed to install. Checking critical packages..." -ForegroundColor Yellow
    
    # Check critical packages individually
    $criticalPackages = @("streamlit", "pandas", "numpy")
    $failed = @()
    
    foreach ($package in $criticalPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $failed += $package
            } else {
                Write-Host "  ✅ $package" -ForegroundColor Green
            }
        } catch {
            $failed += $package
        }
    }
    
    if ($failed.Count -gt 0) {
        Write-Host "❌ Critical packages failed to install: $($failed -join ', ')" -ForegroundColor Red
        Write-Host "Please try running manually: pip install $($failed -join ' ')" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Check optional packages
    $optionalPackages = @("scipy", "plotly", "matplotlib")
    foreach ($package in $optionalPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $package" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️ $package (optional)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ⚠️ $package (optional)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "⚠️ Core packages are available, continuing with startup..." -ForegroundColor Yellow
}

# Check if gui.py exists
if (-not (Test-Path "src\gui.py")) {
    Write-Host "❌ gui.py not found in src directory!" -ForegroundColor Red
    Write-Host "Please ensure the project structure is complete." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the application
Write-Host "🚀 Starting Battery Cycle Analyzer..." -ForegroundColor Green
Write-Host "📝 The application will open in your web browser at http://localhost:8501" -ForegroundColor Cyan
Write-Host "🔴 To stop the application, close this window or press Ctrl+C" -ForegroundColor Yellow
Write-Host ""

try {
    Set-Location src
    python -m streamlit run gui.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
} catch {
    Write-Host "❌ Error starting application: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "• Make sure gui.py is in the src folder" -ForegroundColor Yellow
    Write-Host "• Try: pip install -r config\requirements.txt" -ForegroundColor Yellow
    Write-Host "• Check that no other application is using port 8501" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
} 