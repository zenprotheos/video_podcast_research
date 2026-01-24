@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -MaxAgeMinutes 30
exit /b %ERRORLEVEL%

