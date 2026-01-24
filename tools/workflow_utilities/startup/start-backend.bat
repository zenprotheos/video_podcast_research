@echo off
echo ========================================
echo   VOICESCRIBEAI BACKEND STARTUP
echo ========================================
echo.

cd /d "%~dp0"

echo Starting Flask Backend...
echo Backend will run on: http://localhost:5000
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\workflow_utilities\service_manager.ps1" -Action start-backend

echo.
echo Press any key to close this window
pause > nul
