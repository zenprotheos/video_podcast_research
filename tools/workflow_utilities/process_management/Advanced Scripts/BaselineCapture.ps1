Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

$baselineDir = Join-Path $PSScriptRoot '..\Baseline'
New-Item -Path $baselineDir -ItemType Directory -Force | Out-Null
$baselinePath = Join-Path $baselineDir 'terminal_baseline.json'

$shellNames = @('pwsh','powershell','cmd','conhost','cursor','Code','WindowsTerminal','wt')
$procs = Get-Process | Where-Object { $shellNames -contains $_.Name } | Select-Object Name,Id,MainWindowTitle

$json = $procs | ConvertTo-Json -Depth 2
Set-Content -Path $baselinePath -Value $json -Encoding utf8
Write-Output "Baseline captured to $baselinePath"
return 0

