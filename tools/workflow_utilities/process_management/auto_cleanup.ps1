# Auto-cleanup script for oneshot process management
# Run this to set up automatic cleanup

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Test
)

$ErrorActionPreference = "Stop"

# Paths
$MonitorScript = "$PSScriptRoot\process_monitor.ps1"
$TaskName = "Oneshot_Process_Cleanup"
$TaskDescription = "Automatically cleans up orphaned Python processes for Oneshot"

function Install-AutoCleanup {
    Write-Host "Installing automatic process cleanup..." -ForegroundColor Green

    # Check if monitor script exists
    if (!(Test-Path $MonitorScript)) {
        Write-Error "Monitor script not found at $MonitorScript"
        exit 1
    }

    # Create scheduled task
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$MonitorScript`" -Cleanup"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    try {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description $TaskDescription -RunLevel Highest -Force
        Write-Host "SUCCESS: Auto-cleanup task installed successfully" -ForegroundColor Green
        Write-Host "Task will run every 5 minutes to clean up old processes" -ForegroundColor Yellow
    } catch {
        Write-Error "Failed to install scheduled task: $($_.Exception.Message)"
    }
}

function Uninstall-AutoCleanup {
    Write-Host "Uninstalling automatic process cleanup..." -ForegroundColor Yellow

    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "SUCCESS: Auto-cleanup task uninstalled successfully" -ForegroundColor Green
    } catch {
        Write-Host "Task was not installed or could not be removed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Test-AutoCleanup {
    Write-Host "Testing process cleanup..." -ForegroundColor Cyan

    # Run the monitor script
    try {
        & $MonitorScript
    } catch {
        Write-Error "Test failed: $($_.Exception.Message)"
    }
}

# Main execution
if ($Install) {
    Install-AutoCleanup
} elseif ($Uninstall) {
    Uninstall-AutoCleanup
} elseif ($Test) {
    Test-AutoCleanup
} else {
    Write-Host "Oneshot Auto-Cleanup Utility" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\auto_cleanup.ps1 -Install     # Install automatic cleanup task"
    Write-Host "  .\auto_cleanup.ps1 -Uninstall   # Remove automatic cleanup task"
    Write-Host "  .\auto_cleanup.ps1 -Test        # Test the cleanup functionality"
    Write-Host ""
    Write-Host "Current status:" -ForegroundColor Yellow
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-Host "  SUCCESS: Task installed: $($task.TaskName)" -ForegroundColor Green
        Write-Host "  Next run: $($task.NextRunTime)" -ForegroundColor White
    } catch {
        Write-Host "  ERROR: Task not installed" -ForegroundColor Red
    }
}
