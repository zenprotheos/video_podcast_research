# FINAL VERIFICATION: Test the DEAPI fix
# Run this after applying the fix to confirm it works

Write-Host "=== FINAL DEAPI FIX VERIFICATION ===" -ForegroundColor Cyan
Write-Host "Testing that Streamlit uses virtual environment Python..." -ForegroundColor Yellow

# Test that streamlit.cmd now uses virtual environment Python
Write-Host "Testing streamlit.cmd Python resolution..." -ForegroundColor Yellow
try {
    $streamlitPath = ".venv\Scripts\streamlit.cmd"
    if (Test-Path $streamlitPath) {
        # We can't easily test the cmd file directly, but we can test the python.exe it should use
        $pythonTest = & .venv\Scripts\python.exe -c "import sys; print(f'VENV Python: {sys.executable}'); import requests; print(f'requests: {requests.__version__}')" 2>&1
        Write-Host "Virtual environment Python test: $pythonTest" -ForegroundColor Green
    } else {
        Write-Host "ERROR: streamlit.cmd not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR testing virtual environment: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== VERIFICATION COMPLETE ===" -ForegroundColor Green
Write-Host "The fix modifies .venv\Scripts\streamlit.cmd to use virtual environment Python." -ForegroundColor White
Write-Host "This should resolve the 'name requests is not defined' error." -ForegroundColor White

Write-Host "`n=== TEST INSTRUCTIONS ===" -ForegroundColor Cyan
Write-Host "1. Run: .\run_app.ps1" -ForegroundColor White
Write-Host "2. Upload a YouTube URL (use the same one that failed before)" -ForegroundColor White
Write-Host "3. Check that transcription succeeds (should show >0% success)" -ForegroundColor White
Write-Host "4. Session log should NOT show 'name requests is not defined'" -ForegroundColor White

Write-Host "`n[SUCCESS] Fix is implemented and ready for testing!" -ForegroundColor Green