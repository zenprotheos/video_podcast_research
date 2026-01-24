@echo off
echo ========================================
echo   VOICESCRIBEAI SERVICE SHUTDOWN
echo ========================================
echo.

REM Change to project root directory (two levels up from startup folder)
cd /d "%~dp0..\..\.."

REM Verify we're in the right directory
echo Current directory: %CD%
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\workflow_utilities\service_manager.ps1" -Action stop-all

echo.
echo Press any key to close this window
pause > nul
