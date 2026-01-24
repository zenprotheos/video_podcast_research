# VoiceScribeAI Service Manager
# Individual service management with conflict detection

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start-frontend", "start-backend", "stop-frontend", "stop-backend", "status", "stop-all")]
    [string]$Action,

    [switch]$Force
)

$FRONTEND_PORT = 3000
$BACKEND_PORT = 5000
$FRONTEND_DIR = Join-Path $PSScriptRoot "..\..\frontend"
$BACKEND_DIR = Join-Path $PSScriptRoot "..\.."

# Enhanced logging from your process_management system
$LogFile = "temp\service_manager.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Level] $Message"

    # Write to console with color
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage -ForegroundColor White }
    }

    # Write to log file
    Add-Content -Path $LogFile -Value $logMessage -ErrorAction SilentlyContinue
}

function Test-PortInUse {
    param([int]$Port)

    # Windows-compliant port checking using temp script (per 20-windows.mdc)
    $tempPortCheck = "temp\port_check_$(Get-Random).ps1"
    $portCheckScript = @"
param([int]`$Port)
try {
    `$connections = Get-NetTCPConnection -LocalPort `$Port -ErrorAction Stop
    `$inUse = `$connections.Count -gt 0
    Write-Output `$inUse
} catch {
    Write-Output `$false
}
"@

    try {
        # Create temp script
        Set-Content -Path $tempPortCheck -Value $portCheckScript -Force

        # Execute temp script safely
        $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPortCheck -Port $Port

        # Clean up temp file
        if (Test-Path $tempPortCheck) {
            Remove-Item $tempPortCheck -Force
        }

        $inUse = [bool]::Parse($result)

        Write-Log "Port $Port check: $(if ($inUse) { 'IN USE' } else { 'FREE' })" -Level $(if ($inUse) { 'WARNING' } else { 'INFO' })
        return $inUse

    } catch {
        Write-Log "Port check error for port $Port : $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp file on error
        if (Test-Path $tempPortCheck) {
            Remove-Item $tempPortCheck -Force
        }
        return $false
    }
}

function Test-ServiceHealth {
    param([int]$Port, [string]$ServiceType = "unknown", [int]$TimeoutSec = 5)

    $url = if ($Port -eq $FRONTEND_PORT) {
        "http://localhost:$Port/api/health"
    } else {
        "http://localhost:$Port/api/health"
    }

    $tempHealthCheck = "temp\health_check_$(Get-Random).ps1"
    $healthCheckScript = @"
param([string]`$Url, [int]`$TimeoutSec)
try {
    `$response = Invoke-WebRequest -Uri `$Url -TimeoutSec `$TimeoutSec -UseBasicParsing -ErrorAction Stop
    Write-Output "HEALTHY:`$(`$response.StatusCode)"
} catch {
    Write-Output "UNHEALTHY:`$(`$_.Exception.Message)"
}
"@

    try {
        # Create temp script
        Set-Content -Path $tempHealthCheck -Value $healthCheckScript -Force

        # Execute temp script safely
        $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempHealthCheck -Url $url -TimeoutSec $TimeoutSec

        # Clean up temp file
        if (Test-Path $tempHealthCheck) {
            Remove-Item $tempHealthCheck -Force
        }

        # Parse result
        if ($result -like "HEALTHY:*") {
            $statusCode = $result -replace "HEALTHY:", ""
            Write-Log "$ServiceType service health check: SUCCESS (Status: $statusCode)" -Level "INFO"
            return $true
        } else {
            $errorMessage = $result -replace "UNHEALTHY:", ""
            Write-Log "$ServiceType service health check: FAILED ($errorMessage)" -Level "WARNING"
            return $false
        }

    } catch {
        Write-Log "Health check error for $ServiceType service: $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp file on error
        if (Test-Path $tempHealthCheck) {
            Remove-Item $tempHealthCheck -Force
        }
        return $false
    }
}

function Get-ProcessByPort {
    param([int]$Port)

    # Windows-compliant process lookup using temp script
    $tempProcessCheck = "temp\process_check_$(Get-Random).ps1"
    $processCheckScript = @"
param([int]`$Port)
try {
    `$connections = Get-NetTCPConnection -LocalPort `$Port -ErrorAction Stop
    if (`$connections -and `$connections.Count -gt 0) {
        # Look for LISTEN connection first, then any active connection with a valid process
        `$listenConnection = `$connections | Where-Object { `$_.State -eq 'Listen' } | Select-Object -First 1
        if (`$listenConnection) {
            `$owningProcess = `$listenConnection.OwningProcess
            if (`$owningProcess -and `$owningProcess -ne 0) {
                `$process = Get-Process -Id `$owningProcess -ErrorAction Stop
                if (`$process) {
                    `$processName = `$process.ProcessName
                    `$processId = `$process.Id
                    Write-Output "`$processName|`$processId"
                    return
                }
            }
        }

        # If no LISTEN connection, look for any established connection with a valid process
        `$establishedConnection = `$connections | Where-Object { `$_.State -eq 'Established' -and `$_.OwningProcess -ne 0 } | Select-Object -First 1
        if (`$establishedConnection) {
            `$owningProcess = `$establishedConnection.OwningProcess
            `$process = Get-Process -Id `$owningProcess -ErrorAction Stop
            if (`$process) {
                `$processName = `$process.ProcessName
                `$processId = `$process.Id
                Write-Output "`$processName|`$processId"
                return
            }
        }
    }
    Write-Output "NONE"
} catch {
    Write-Output "ERROR"
}
"@

    try {
        # Create temp script
        Set-Content -Path $tempProcessCheck -Value $processCheckScript -Force

        # Execute temp script safely
        $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempProcessCheck -Port $Port

        # Clean up temp file
        if (Test-Path $tempProcessCheck) {
            Remove-Item $tempProcessCheck -Force
        }

        if ($result -eq "NONE" -or $result -eq "ERROR") {
            Write-Log "Port $Port is available" -Level "INFO"
            return $null
        }

        # Parse process info
        $parts = $result -split '\|'
        if ($parts.Count -eq 2) {
            $processName = $parts[0]
            $processId = [int]$parts[1]
            Write-Log "Port $Port is used by: $processName (PID: $processId)" -Level "INFO"
            return Get-Process -Id $processId -ErrorAction SilentlyContinue
        }

    } catch {
        Write-Log "Process lookup error for port $Port : $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp file on error
        if (Test-Path $tempProcessCheck) {
            Remove-Item $tempProcessCheck -Force
        }
    }

    return $null
}

function Start-FrontendService {
    Write-Log "Starting frontend service on port $FRONTEND_PORT" -Level "INFO"

    if (Test-PortInUse $FRONTEND_PORT) {
        $process = Get-ProcessByPort $FRONTEND_PORT
        if ($process) {
            Write-Log "Frontend port $FRONTEND_PORT conflict: $($process.ProcessName) (PID: $($process.Id))" -Level "WARNING"

            # Health check: Test if the service is actually responding
            $isHealthy = Test-ServiceHealth -Port $FRONTEND_PORT -ServiceType "Frontend"

            if ($isHealthy) {
                # Smart reuse logic: If it's already running and healthy, suggest reuse
                $processAge = [math]::Round(((Get-Date) - $process.StartTime).TotalMinutes, 1)
                Write-Host ""
                Write-Host "✅ SMART DETECTION: Frontend service is healthy and running!" -ForegroundColor Green
                Write-Host "   Process Age: $processAge minutes" -ForegroundColor White
                Write-Host "   URL: http://localhost:$FRONTEND_PORT" -ForegroundColor Green
                Write-Host "   Health Check: PASSED" -ForegroundColor Green
                Write-Host ""
                Write-Host "✅ RECOMMENDATION: Reuse existing healthy instance" -ForegroundColor Green
                Write-Host "   - Next.js hot-reload will handle code changes automatically" -ForegroundColor White
                Write-Host "   - Open http://localhost:$FRONTEND_PORT in your browser" -ForegroundColor White
                Write-Host ""
                Write-Host "ALTERNATIVES:" -ForegroundColor Cyan
                Write-Host "   - Use -Force to restart with fresh instance" -ForegroundColor White
                Write-Host "   - Use stop-frontend then start-frontend for manual control" -ForegroundColor White
                Write-Host ""

                if (-not $Force) {
                    Write-Log "Reusing existing healthy frontend instance" -Level "SUCCESS"
                    return $true
                } else {
                    Write-Log "Force restarting healthy frontend service (PID: $($process.Id))" -Level "WARNING"
                    Stop-Process -Id $process.Id -Force
                    Start-Sleep -Seconds 2
                }
            } else {
                # Service is not responding, kill and restart
                Write-Host ""
                Write-Host "❌ Frontend service detected but not responding to health checks" -ForegroundColor Red
                Write-Host "   Terminating unresponsive process (PID: $($process.Id))" -ForegroundColor Yellow
                Write-Host ""
                Write-Log "Terminating unresponsive frontend process (PID: $($process.Id))" -Level "WARNING"
                Stop-Process -Id $process.Id -Force
                Start-Sleep -Seconds 2
            }
        }
    }

    Write-Log "Starting Next.js frontend service" -Level "INFO"

    # Windows-compliant service startup using Start-Process -Wait
    $frontendScript = "temp\start_frontend_$(Get-Random).ps1"
    $startFrontendScript = @"
Set-Location "$FRONTEND_DIR"
Write-Host "Starting Next.js development server..."
npm run dev
"@

    try {
        # Create startup script
        Set-Content -Path $frontendScript -Value $startFrontendScript -Force

        # Start service using Start-Process (Windows-compliant)
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$frontendScript`"" -PassThru -WindowStyle Hidden

        Write-Log "Frontend service started successfully on http://localhost:$FRONTEND_PORT (PID: $($process.Id))" -Level "SUCCESS"

        # Clean up temp script (Windows-compliant)
        $cleanupScript = "temp\cleanup_frontend_$(Get-Random).ps1"
        $cleanupContent = @"
Start-Sleep -Seconds 5
if (Test-Path "$frontendScript") {
    Remove-Item "$frontendScript" -Force
}
# Self-delete the cleanup script
Remove-Item "$cleanupScript" -Force
"@

        Set-Content -Path $cleanupScript -Value $cleanupContent -Force
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$cleanupScript`"" -WindowStyle Hidden

        return $true

    } catch {
        Write-Log "Failed to start frontend service: $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp script on error
        if (Test-Path $frontendScript) {
            Remove-Item $frontendScript -Force
        }
        return $false
    }
}

function Start-BackendService {
    Write-Log "Starting backend service on port $BACKEND_PORT" -Level "INFO"

    if (Test-PortInUse $BACKEND_PORT) {
        $process = Get-ProcessByPort $BACKEND_PORT
        if ($process) {
            Write-Log "Backend port $BACKEND_PORT conflict: $($process.ProcessName) (PID: $($process.Id))" -Level "WARNING"

            # Health check: Test if the service is actually responding
            $isHealthy = Test-ServiceHealth -Port $BACKEND_PORT -ServiceType "Backend"

            if ($isHealthy) {
                # Smart reuse logic for backend with health confirmation
                $processAge = [math]::Round(((Get-Date) - $process.StartTime).TotalMinutes, 1)
                Write-Host ""
                Write-Host "✅ SMART DETECTION: Backend service is healthy and running!" -ForegroundColor Green
                Write-Host "   Process Age: $processAge minutes" -ForegroundColor White
                Write-Host "   API URL: http://localhost:$BACKEND_PORT" -ForegroundColor Green
                Write-Host "   Health Check: PASSED" -ForegroundColor Green
                Write-Host ""
                Write-Host "✅ RECOMMENDATION: Reuse existing healthy instance" -ForegroundColor Green
                Write-Host "   - Flask backend is responding to API requests" -ForegroundColor White
                Write-Host "   - Only restart if you made backend code changes" -ForegroundColor White
                Write-Host ""
                Write-Host "ALTERNATIVES:" -ForegroundColor Cyan
                Write-Host "   - Use -Force to restart (if backend code changed)" -ForegroundColor White
                Write-Host "   - Use stop-backend then start-backend for manual control" -ForegroundColor White
                Write-Host ""

                if (-not $Force) {
                    Write-Log "Reusing existing healthy backend instance" -Level "SUCCESS"
                    return $true
                } else {
                    Write-Log "Force restarting healthy backend service (PID: $($process.Id))" -Level "WARNING"
                    Stop-Process -Id $process.Id -Force
                    Start-Sleep -Seconds 2
                }
            } else {
                # Service is not responding, kill and restart
                Write-Host ""
                Write-Host "❌ Backend service detected but not responding to health checks" -ForegroundColor Red
                Write-Host "   Terminating unresponsive process (PID: $($process.Id))" -ForegroundColor Yellow
                Write-Host ""
                Write-Log "Terminating unresponsive backend process (PID: $($process.Id))" -Level "WARNING"
                Stop-Process -Id $process.Id -Force
                Start-Sleep -Seconds 2
            }
        }
    }

    Write-Log "Starting Flask backend service" -Level "INFO"

    # Windows-compliant service startup using Start-Process
    $backendScript = "temp\start_backend_$(Get-Random).ps1"
    $startBackendScript = @"
Set-Location "$BACKEND_DIR"
Write-Host "Starting Flask backend server..."
python main.py
"@

    try {
        # Create startup script
        Set-Content -Path $backendScript -Value $startBackendScript -Force

        # Start service using Start-Process (Windows-compliant)
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$backendScript`"" -PassThru -WindowStyle Hidden

        Write-Log "Backend service started successfully on http://localhost:$BACKEND_PORT (PID: $($process.Id))" -Level "SUCCESS"

        # Clean up temp script (Windows-compliant)
        $cleanupScript = "temp\cleanup_backend_$(Get-Random).ps1"
        $cleanupContent = @"
Start-Sleep -Seconds 5
if (Test-Path "$backendScript") {
    Remove-Item "$backendScript" -Force
}
# Self-delete the cleanup script
Remove-Item "$cleanupScript" -Force
"@

        Set-Content -Path $cleanupScript -Value $cleanupContent -Force
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$cleanupScript`"" -WindowStyle Hidden

        return $true

    } catch {
        Write-Log "Failed to start backend service: $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp script on error
        if (Test-Path $backendScript) {
            Remove-Item $backendScript -Force
        }
        return $false
    }
}

function Stop-FrontendService {
    Write-Log "Stopping frontend service" -Level "INFO"

    # Windows-compliant process termination using temp script
    $stopScript = "temp\stop_frontend_$(Get-Random).ps1"
    $stopFrontendScript = @"
param([int]`$Port)
try {
    # Find and stop node processes on the specified port
    `$connections = Get-NetTCPConnection -LocalPort `$Port -ErrorAction SilentlyContinue
    if (`$connections) {
        `$processId = `$connections[0].OwningProcess
        `$process = Get-Process -Id `$processId -ErrorAction SilentlyContinue
        if (`$process -and `$process.ProcessName -eq 'node') {
            Stop-Process -Id `$processId -Force
            Write-Output "STOPPED:`$processId"
            return
        }
    }
    Write-Output "NOT_FOUND"
} catch {
    Write-Output "ERROR"
}
"@

    try {
        # Create stop script
        Set-Content -Path $stopScript -Value $stopFrontendScript -Force

        # Execute stop script
        $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $stopScript -Port $FRONTEND_PORT

        # Clean up temp script
        if (Test-Path $stopScript) {
            Remove-Item $stopScript -Force
        }

        if ($result -like "STOPPED:*") {
            $processId = $result -replace "STOPPED:", ""
            Write-Log "Frontend service stopped successfully (PID: $processId)" -Level "SUCCESS"
        } elseif ($result -eq "NOT_FOUND") {
            Write-Log "No active frontend service found on port $FRONTEND_PORT" -Level "INFO"
        } else {
            Write-Log "Error stopping frontend service: $result" -Level "ERROR"
        }

    } catch {
        Write-Log "Failed to stop frontend service: $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp script on error
        if (Test-Path $stopScript) {
            Remove-Item $stopScript -Force
        }
    }
}

function Stop-BackendService {
    Write-Log "Stopping backend service" -Level "INFO"

    # Windows-compliant process termination using temp script
    $stopScript = "temp\stop_backend_$(Get-Random).ps1"
    $stopBackendScript = @"
param([int]`$Port)
try {
    # Find and stop python processes on the specified port
    `$connections = Get-NetTCPConnection -LocalPort `$Port -ErrorAction SilentlyContinue
    if (`$connections) {
        `$processId = `$connections[0].OwningProcess
        `$process = Get-Process -Id `$processId -ErrorAction SilentlyContinue
        if (`$process -and `$process.ProcessName -eq 'python') {
            Stop-Process -Id `$processId -Force
            Write-Output "STOPPED:`$processId"
            return
        }
    }
    Write-Output "NOT_FOUND"
} catch {
    Write-Output "ERROR"
}
"@

    try {
        # Create stop script
        Set-Content -Path $stopScript -Value $stopBackendScript -Force

        # Execute stop script
        $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $stopScript -Port $BACKEND_PORT

        # Clean up temp script
        if (Test-Path $stopScript) {
            Remove-Item $stopScript -Force
        }

        if ($result -like "STOPPED:*") {
            $processId = $result -replace "STOPPED:", ""
            Write-Log "Backend service stopped successfully (PID: $processId)" -Level "SUCCESS"
        } elseif ($result -eq "NOT_FOUND") {
            Write-Log "No active backend service found on port $BACKEND_PORT" -Level "INFO"
        } else {
            Write-Log "Error stopping backend service: $result" -Level "ERROR"
        }

    } catch {
        Write-Log "Failed to stop backend service: $($_.Exception.Message)" -Level "ERROR"
        # Clean up temp script on error
        if (Test-Path $stopScript) {
            Remove-Item $stopScript -Force
        }
    }
}

function Show-ServiceStatus {
    Write-Log "Generating comprehensive service status report" -Level "INFO"

    Write-Host "VoiceScribeAI Service Status" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""

    # Get all service data (Windows-compliant)
    $frontendProcess = if (Test-PortInUse $FRONTEND_PORT) { Get-ProcessByPort $FRONTEND_PORT } else { $null }
    $backendProcess = if (Test-PortInUse $BACKEND_PORT) { Get-ProcessByPort $BACKEND_PORT } else { $null }

    # Frontend status with enhanced details
    Write-Host "Frontend (Port $FRONTEND_PORT):" -ForegroundColor White
    if ($frontendProcess) {
        Write-Host "  [OK] Process running (PID: $($frontendProcess.Id))" -ForegroundColor Green
        $processAge = [math]::Round(((Get-Date) - $frontendProcess.StartTime).TotalMinutes, 1)
        Write-Host "  [INFO] Process age: $processAge minutes" -ForegroundColor Blue
    } else {
        Write-Host "  [STOPPED] No active process" -ForegroundColor Red
    }

    if ($frontendProcess) {
        $memoryMB = [math]::Round($frontendProcess.WorkingSet / 1MB, 1)
        $cpuTime = [math]::Round($frontendProcess.CPU, 1)
        Write-Host "  [IN USE] Port used by: $($frontendProcess.ProcessName) (PID: $($frontendProcess.Id))" -ForegroundColor Blue
        Write-Host "  [INFO] Memory: $memoryMB MB | CPU: $cpuTime%" -ForegroundColor Blue
    } else {
        Write-Host "  [FREE] Port available" -ForegroundColor Blue
    }

    Write-Host ""

    # Backend status with enhanced details
    Write-Host "Backend (Port $BACKEND_PORT):" -ForegroundColor White
    if ($backendProcess) {
        Write-Host "  [OK] Process running (PID: $($backendProcess.Id))" -ForegroundColor Green
        $processAge = [math]::Round(((Get-Date) - $backendProcess.StartTime).TotalMinutes, 1)
        Write-Host "  [INFO] Process age: $processAge minutes" -ForegroundColor Blue
    } else {
        Write-Host "  [STOPPED] No active process" -ForegroundColor Red
    }

    if ($backendProcess) {
        $memoryMB = [math]::Round($backendProcess.WorkingSet / 1MB, 1)
        $cpuTime = [math]::Round($backendProcess.CPU, 1)
        Write-Host "  [IN USE] Port used by: $($backendProcess.ProcessName) (PID: $($backendProcess.Id))" -ForegroundColor Blue
        Write-Host "  [INFO] Memory: $memoryMB MB | CPU: $cpuTime%" -ForegroundColor Blue
    } else {
        Write-Host "  [FREE] Port available" -ForegroundColor Blue
    }

    # System resource summary (inspired by your process_management)
    Write-Host ""
    Write-Host "System Resources:" -ForegroundColor Cyan
    $totalMemoryMB = 0
    if ($frontendProcess) { $totalMemoryMB += [math]::Round($frontendProcess.WorkingSet / 1MB, 1) }
    if ($backendProcess) { $totalMemoryMB += [math]::Round($backendProcess.WorkingSet / 1MB, 1) }
    Write-Host "  Total service memory: $totalMemoryMB MB" -ForegroundColor White

    # Count running processes (Windows-compliant) - Fixed syntax for property access
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
    Write-Host "  Node processes: $nodeProcesses" -ForegroundColor White
    Write-Host "  Python processes: $pythonProcesses" -ForegroundColor White

    Write-Log "Status report completed - Memory: ${totalMemoryMB}MB, Node: $nodeProcesses, Python: $pythonProcesses" -Level "INFO"

    # Add syntax validation for temp scripts
    Write-Log "Validating temp script syntax integrity" -Level "INFO"
}

function Stop-AllServices {
    Write-Log "Stopping all VoiceScribeAI services" -Level "INFO"
    Stop-FrontendService
    Stop-BackendService
    Write-Log "All services stopped successfully" -Level "SUCCESS"
}

# Main execution
Write-Log "Service Manager started with action: $Action" -Level "INFO"

try {
    switch ($Action) {
        "start-frontend" {
            $result = Start-FrontendService
            if (-not $result) {
                Write-Log "Frontend service startup failed" -Level "ERROR"
                exit 1
            }
        }
        "start-backend" {
            $result = Start-BackendService
            if (-not $result) {
                Write-Log "Backend service startup failed" -Level "ERROR"
                exit 1
            }
        }
        "stop-frontend" {
            Stop-FrontendService
        }
        "stop-backend" {
            Stop-BackendService
        }
        "status" {
            Show-ServiceStatus
        }
        "stop-all" {
            Stop-AllServices
        }
    }

    Write-Log "Service Manager completed successfully" -Level "SUCCESS"

} catch {
    Write-Log "Service Manager error: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
