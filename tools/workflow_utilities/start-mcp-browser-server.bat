@echo off
REM VoiceScribeAI MCP Browser Server Startup Script
REM Starts MCP browser server for automated client-side log capture

echo ========================================
echo   STARTING MCP BROWSER SERVER
echo ========================================
echo.

cd /d "%~dp0.."

echo Checking for Node.js...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found in PATH
    echo Please install Node.js and add it to your PATH
    pause
    exit /b 1
)

echo Starting MCP Browser Server on port 9222...
echo This will enable automated client-side log capture
echo Using: @agentdeskai/browser-tools-server@latest
echo.

npx @agentdeskai/browser-tools-server@latest

echo.
echo MCP Browser Server stopped.
echo Use this server for automated client-side debugging with:
echo - mcp_browser-tools_getConsoleLogs()
echo - mcp_browser-tools_getNetworkErrors()
echo - mcp_browser-tools_runPerformanceAudit()
echo.

pause
