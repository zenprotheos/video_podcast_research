@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
set MODE=%1
if /I "%MODE%"=="report" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -ReportOnly
  exit /b %ERRORLEVEL%
)
if /I "%MODE%"=="safe" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -SafeMode
  exit /b %ERRORLEVEL%
)
if /I "%MODE%"=="clean" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -MaxAgeMinutes 15
  exit /b %ERRORLEVEL%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..\Advanced Scripts\targeted_cleanup.ps1" -MaxAgeMinutes 30
exit /b %ERRORLEVEL%

