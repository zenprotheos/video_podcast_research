@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -ReportOnly
exit /b %ERRORLEVEL%

