# PowerShell script to run the Streamlit app
# Usage: .\run_app.ps1

$ErrorActionPreference = "Stop"

Write-Host "Starting Bulk Transcribe MVP..." -ForegroundColor Cyan

# Check if venv exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Error: Virtual environment not found. Run: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# Check for DEAPI key
if (-not $env:DEAPI_API_KEY) {
    Write-Host "Warning: DEAPI_API_KEY not set. DEAPI features will not work." -ForegroundColor Yellow
    Write-Host "Set it with: `$env:DEAPI_API_KEY='YOUR_KEY'" -ForegroundColor Yellow
}

# FIX: Isolate PATH to prevent system Python interference
# This resolves the "name 'requests' is not defined" error in DEAPI transcription
Write-Host "Isolating Python environment PATH..." -ForegroundColor Cyan

# Get virtual environment paths
$venvScriptsPath = Resolve-Path ".venv\Scripts"
$venvLibPath = Resolve-Path ".venv\Lib\site-packages"

# Create clean PATH with virtual environment first
$originalPath = $env:PATH
$cleanPath = "$venvScriptsPath;$venvLibPath;$env:PATH"

# Set isolated environment
$env:PATH = $cleanPath
$env:PYTHONPATH = $venvLibPath
$env:PYTHONHOME = $null  # Clear PYTHONHOME to prevent conflicts

Write-Host "Environment isolated - virtual environment paths prioritized" -ForegroundColor Green
Write-Host "Venv Scripts: $venvScriptsPath" -ForegroundColor Gray
Write-Host "Venv Lib: $venvLibPath" -ForegroundColor Gray

# Test the isolated environment
Write-Host "Testing isolated environment..." -ForegroundColor Yellow
try {
    $testResult = & $venvScriptsPath\python.exe -c "import sys; print(f'Python: {sys.executable}'); import requests; print(f'requests: {requests.__version__}')" 2>&1
    Write-Host "Environment test successful: $testResult" -ForegroundColor Green
} catch {
    Write-Host "Environment test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Run Streamlit with isolated environment
# Use more explicit environment variable approach
try {
    # Set environment variables that Streamlit should respect
    $env:STREAMLIT_SERVER_HEADLESS = "true"
    $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

    # Try running with explicit environment variables
    Write-Host "Launching Streamlit with isolated environment..." -ForegroundColor Green
    & .\.venv\Scripts\python.exe -m streamlit run app.py
} finally {
    # Restore original PATH when done
    $env:PATH = $originalPath
    $env:PYTHONPATH = $null
    Write-Host "Environment restored" -ForegroundColor Cyan
}
