@echo off
REM Quick MCP Browser Server Health Check
REM Checks if server is running on port 9222 without starting processes

echo Checking MCP Browser Server health...
echo.

REM Check if port 9222 is in use (Windows)
netstat -ano | findstr :9222 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MCP Browser Server is RUNNING on port 9222
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9222') do (
        echo Server Process ID: %%a
        goto :server_running
    )
) else (
    echo ❌ MCP Browser Server is NOT running on port 9222
    goto :server_not_running
)

:server_running
echo.
echo You can now use MCP browser tools:
echo - mcp_browser-tools_getConsoleLogs()
echo - mcp_browser-tools_getNetworkErrors()
echo - mcp_browser-tools_runPerformanceAudit()
goto :end

:server_not_running
echo.
echo To start MCP Browser Server, run:
echo tools/workflow_utilities/start-mcp-browser-server.bat
echo.
echo Or manually:
echo npx @agentdeskai/browser-tools-server@latest
goto :end

:end
echo.
echo Health check complete.
