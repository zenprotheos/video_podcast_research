# DEAPI PATH Isolation Fix Verification Script
# Tests the PATH isolation fix before running the full app

Write-Host "=== DEAPI PATH Isolation Fix Verification ===" -ForegroundColor Cyan

# Step 1: Check current environment
Write-Host "`n1. Checking current environment..." -ForegroundColor Yellow
Write-Host "Current PATH entries with 'python' (first 3):"
$pythonPaths = $env:PATH -split ';' | Where-Object { $_ -like '*python*' } | Select-Object -First 3
$pythonPaths | ForEach-Object { Write-Host "  $_" }

# Step 2: Simulate the PATH isolation logic
Write-Host "`n2. Simulating PATH isolation..." -ForegroundColor Yellow

$venvScriptsPath = Resolve-Path ".venv\Scripts" -ErrorAction SilentlyContinue
$venvLibPath = Resolve-Path ".venv\Lib\site-packages" -ErrorAction SilentlyContinue

if (-not $venvScriptsPath -or -not $venvLibPath) {
    Write-Host "ERROR: Virtual environment not found or incomplete" -ForegroundColor Red
    exit 1
}

# Create isolated PATH (same logic as run_app.ps1)
$originalPath = $env:PATH
$isolatedPath = "$venvScriptsPath;$venvLibPath;$env:PATH"

Write-Host "Virtual environment Scripts path: $venvScriptsPath" -ForegroundColor Green
Write-Host "Virtual environment Lib path: $venvLibPath" -ForegroundColor Green
Write-Host "Isolated PATH will prioritize virtual environment" -ForegroundColor Green

# Step 3: Test with isolated PATH
Write-Host "`n3. Testing with isolated PATH..." -ForegroundColor Yellow

# Temporarily set isolated PATH
$env:PATH = $isolatedPath
$env:PYTHONPATH = $venvLibPath
$env:PYTHONHOME = $null

try {
    # Test Python import
    $testResult = & $venvScriptsPath\python.exe -c "import requests; print('SUCCESS: requests version ' + requests.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python import test: $testResult" -ForegroundColor Green
    } else {
        Write-Host "Python import test FAILED: $testResult" -ForegroundColor Red
        exit 1
    }

    # Test that we're using the right Python
    $pythonPath = & $venvScriptsPath\python.exe -c "import sys; print(sys.executable)" 2>&1
    Write-Host "Python executable: $pythonPath" -ForegroundColor Green

    $inVenv = & $venvScriptsPath\python.exe -c "import sys; print('true' if sys.prefix != sys.base_prefix else 'false')" 2>&1
    Write-Host "Running in virtual environment: $inVenv" -ForegroundColor Green

} finally {
    # Restore original PATH
    $env:PATH = $originalPath
    $env:PYTHONPATH = $null
    Write-Host "Environment restored" -ForegroundColor Cyan
}

# Step 4: Verify fix is ready
Write-Host "`n4. Fix verification complete!" -ForegroundColor Green
Write-Host "The PATH isolation fix should resolve the DEAPI import error." -ForegroundColor Green
Write-Host "Run '.\run_app.ps1' to test with the full application." -ForegroundColor White

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. Run: .\run_app.ps1" -ForegroundColor White
Write-Host "2. Go to Bulk Transcribe page" -ForegroundColor White
Write-Host "3. Test with sample YouTube URLs" -ForegroundColor White
Write-Host "4. Verify transcriptions succeed (should see >0% success rate)" -ForegroundColor White

Write-Host "`n[SUCCESS] Fix is ready for testing!" -ForegroundColor Green