param(
  [int]$MaxAgeMinutes = 30,
  [switch]$ReportOnly,
  [switch]$SafeMode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'
Import-Module (Join-Path $PSScriptRoot 'ProcessManagement.psm1') -Force

$logDir = Join-Path $PSScriptRoot '..\Logs\temp'
New-Item -Path $logDir -ItemType Directory -Force | Out-Null
$log = Join-Path $logDir 'targeted_cleanup.log'

function Write-Log($msg) { (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " " + $msg | Out-File -FilePath $log -Append -Encoding utf8 }

Write-Log "Run: MaxAge=$MaxAgeMinutes ReportOnly=$ReportOnly SafeMode=$SafeMode"

$targets = Remove-DevProcesses -MaxAgeMinutes $MaxAgeMinutes -ReportOnly:$ReportOnly -SafeMode:$SafeMode

if ($ReportOnly -or $SafeMode) {
  $targets | Select-Object Name, Id, WS_MB, CPU, StartTime, AgeMin, IsOld | Format-Table -AutoSize | Out-String | Write-Output
  return 0
}

# Actual cleanup
Remove-DevProcesses -MaxAgeMinutes $MaxAgeMinutes | Out-Null
Write-Log "Cleanup complete"
return 0

