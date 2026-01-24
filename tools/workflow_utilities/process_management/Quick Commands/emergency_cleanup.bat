@echo off
echo [Emergency] Killing ALL python.exe processes...
taskkill /F /IM python.exe /T >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo No python.exe processes found or access denied.
) else (
  echo python.exe processes terminated.
)
exit /b 0

