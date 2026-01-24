@echo off
REM FULL SYSTEM CLEANUP - Complete process and terminal cleanup
REM This script performs comprehensive cleanup of all running processes and terminals

echo.
echo ========================================
echo   FULL SYSTEM CLEANUP STARTED
echo ========================================
echo.

REM Get initial status
echo [BEFORE CLEANUP STATUS]
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { $processes = Get-Process -Name python -ErrorAction SilentlyContinue; Write-Host \"Python processes: $($processes.Count)\"; $psProcs = Get-Process -Name powershell -ErrorAction SilentlyContinue; $chProcs = Get-Process -Name conhost -ErrorAction SilentlyContinue; Write-Host \"PowerShell processes: $($psProcs.Count)\"; Write-Host \"Console Host processes: $($chProcs.Count)\"; $totalMem = 0; if ($psProcs.Count -gt 0) { $totalMem += ($psProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB }; if ($chProcs.Count -gt 0) { $totalMem += ($chProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB }; Write-Host \"Terminal memory usage: $([math]::Round($totalMem, 1)) MB\" }"
echo.

echo ========================================
echo   PHASE 1: EMERGENCY PYTHON CLEANUP
echo ========================================
echo.

REM Run emergency Python cleanup (terminates ALL Python processes older than 2 minutes)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Import-Module '%~dp0Advanced Scripts\ProcessManagement.psm1'; Invoke-EmergencyCleanup }"

echo.
echo ========================================
echo   PHASE 2: EMERGENCY TERMINAL CLEANUP
echo ========================================
echo.

REM Run emergency terminal cleanup (force cleanup ALL terminals, keeping only most recent) and respect baseline if present
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Import-Module '%~dp0Advanced Scripts\ProcessManagement.psm1'; Invoke-TerminalCleanup -MaxAgeMinutes 5 -RespectBaseline }"

echo.
echo ========================================
echo   PHASE 3: FINAL VERIFICATION
echo ========================================
echo.

REM Get final status
echo [AFTER CLEANUP STATUS]
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$processes = Get-Process -Name python -ErrorAction SilentlyContinue; Write-Host \"Python processes: $($processes.Count)\"; $psProcs = Get-Process -Name powershell -ErrorAction SilentlyContinue; $chProcs = Get-Process -Name conhost -ErrorAction SilentlyContinue; Write-Host \"PowerShell processes: $($psProcs.Count)\"; Write-Host \"Console Host processes: $($chProcs.Count)\"; $totalMem = 0; if ($psProcs.Count -gt 0) { $totalMem += ($psProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB }; if ($chProcs.Count -gt 0) { $totalMem += ($chProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB }; Write-Host \"Terminal memory usage: $([math]::Round($totalMem, 1)) MB\""

echo.
echo ========================================
echo   CLEANUP TARGETS
echo ========================================
echo ✓ Target: ^< 3 PowerShell processes
echo ✓ Target: ^< 5 Console Host processes
echo ✓ Target: ^< 200 MB terminal memory
echo.
echo Check the [AFTER CLEANUP STATUS] above to verify achievement.

echo.
echo ========================================
echo   FULL CLEANUP COMPLETE
echo ========================================
echo.

REM Check logs
echo Review cleanup logs for detailed information:
echo - temp/process_monitor.log (Python cleanup)
echo - temp/terminal_cleanup.log (Terminal cleanup)
echo.

pause
