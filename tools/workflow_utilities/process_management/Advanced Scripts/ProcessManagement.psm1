function Get-DevProcesses {
  [CmdletBinding()]
  param(
    [int]$MaxAgeMinutes = 30
  )
  $since = (Get-Date).AddMinutes(-$MaxAgeMinutes)
  $names = @('node','npm','python','python3','py','uvicorn','gunicorn','next','chrome','msedge','powershell','pwsh','cmd')
  $procs = Get-Process | Where-Object { $names -contains $_.Name.ToLower() }
  foreach ($p in $procs) {
    $start = $null
    try { $start = $p.StartTime } catch { }
    [PSCustomObject]@{
      Name = $p.Name
      Id = $p.Id
      CPU = $p.CPU
      WS_MB = [math]::Round(($p.WorkingSet64/1MB),0)
      StartTime = $start
      AgeMin = if ($start) { [int]((New-TimeSpan -Start $start -End (Get-Date)).TotalMinutes) } else { $null }
      IsOld = if ($start) { $start -lt $since } else { $false }
    }
  }
}

function Read-Baseline {
  $path = Join-Path $PSScriptRoot '..\Baseline\terminal_baseline.json' | Resolve-Path -ErrorAction SilentlyContinue
  if (!$path) { return @() }
  try { (Get-Content $path | ConvertFrom-Json) } catch { @() }
}

function Remove-DevProcesses {
  [CmdletBinding(SupportsShouldProcess)]
  param(
    [int]$MaxAgeMinutes = 30,
    [switch]$ReportOnly,
    [switch]$SafeMode
  )

  $baseline = Read-Baseline
  $baselinePids = @()
  if ($baseline) { $baselinePids = $baseline | ForEach-Object { $_.Pid } }

  $procs = Get-DevProcesses -MaxAgeMinutes $MaxAgeMinutes
  $targets = $procs | Where-Object {
    $_.IsOld -and ($baselinePids -notcontains $_.Id)
  }

  if ($ReportOnly) {
    return $targets | Sort-Object WS_MB -Descending
  }

  foreach ($t in $targets) {
    if ($SafeMode) {
      Write-Host "[SAFE] Would kill $($t.Name) (PID $($t.Id)) AgeMin=$($t.AgeMin) WS_MB=$($t.WS_MB)" -ForegroundColor Yellow
      continue
    }
    try {
      if ($PSCmdlet.ShouldProcess("$($t.Name)#$($t.Id)", 'Stop-Process')) {
        Stop-Process -Id $t.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[KILLED] $($t.Name) (PID $($t.Id))" -ForegroundColor Green
      }
    } catch {
      Write-Host "[SKIP] $($t.Name) (PID $($t.Id)) - $_" -ForegroundColor DarkGray
    }
  }
}

Export-ModuleMember -Function Get-DevProcesses, Remove-DevProcesses, Read-Baseline

