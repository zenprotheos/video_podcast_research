@echo off
echo ========================================
echo   VOICESCRIBEAI FRONTEND STARTUP
echo ========================================
echo.

cd /d "%~dp0"

echo Starting Next.js Frontend...
echo Frontend will run on: http://localhost:3000
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\workflow_utilities\service_manager.ps1" -Action start-frontend

echo.
echo Press any key to close this window
pause > nul
