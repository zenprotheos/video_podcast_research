param(
  [switch]$Cleanup,
  [switch]$Monitor,
  [switch]$ReportOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'
Import-Module (Join-Path $PSScriptRoot 'ProcessManagement.psm1') -Force

$logDir = Join-Path $PSScriptRoot '..\Logs\temp'
New-Item -Path $logDir -ItemType Directory -Force | Out-Null
$log = Join-Path $logDir 'process_monitor.log'

function Write-Log($msg) {
  (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " " + $msg | Out-File -FilePath $log -Append -Encoding utf8
}

$procs = Get-DevProcesses -MaxAgeMinutes 30 | Sort-Object WS_MB -Descending

if ($ReportOnly) {
  $procs | Select-Object Name, Id, WS_MB, CPU, StartTime, AgeMin, IsOld | Format-Table -AutoSize | Out-String | Write-Output
  return 0
}

if ($Cleanup) {
  Write-Log "Cleanup requested"
  Remove-DevProcesses -MaxAgeMinutes 30 | Out-Null
}

if ($Monitor) {
  $procs | Select-Object Name, Id, WS_MB, CPU, StartTime, AgeMin, IsOld | Format-Table -AutoSize | Out-String | Write-Output
  return 0
}

$summary = @{
  Total = $procs.Count
  Over200MB = ($procs | Where-Object { $_.WS_MB -gt 200 }).Count
  Python = ($procs | Where-Object { $_.Name -match 'python' }).Count
  PowerShell = ($procs | Where-Object { $_.Name -match 'powershell|pwsh' }).Count
}
"Totals: $($summary.Total) | >200MB: $($summary.Over200MB) | Python: $($summary.Python) | PowerShell: $($summary.PowerShell)" | Write-Output
return 0

