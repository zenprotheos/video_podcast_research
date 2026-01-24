@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\BaselineCapture.ps1"
exit /b %ERRORLEVEL%

