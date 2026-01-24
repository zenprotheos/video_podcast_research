@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\process_monitor.ps1" -ReportOnly
exit /b %ERRORLEVEL%

