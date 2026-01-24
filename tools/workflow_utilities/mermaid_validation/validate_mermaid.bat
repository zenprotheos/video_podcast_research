@echo off
REM Batch wrapper for Mermaid diagram validation
REM Usage: validate_mermaid.bat [path] [-recurse]

if "%~1"=="" (
    echo Usage: %0 [path] [-recurse]
    echo Example: %0 "tasks/my_task"
    echo Example: %0 "." -recurse
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "VALIDATE_SCRIPT=%SCRIPT_DIR%validate_mermaid.ps1"

if "%~2"=="-recurse" (
    powershell.exe -ExecutionPolicy Bypass -File "%VALIDATE_SCRIPT%" -Path "%~1" -Recurse
) else (
    powershell.exe -ExecutionPolicy Bypass -File "%VALIDATE_SCRIPT%" -Path "%~1"
)


