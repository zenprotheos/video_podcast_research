param([string]$Format = 'taskFolder')
$now = Get-Date
switch ($Format) {
    'taskFolder' { (Get-Date).ToString('yyyy-MM-dd') }
    'iso' { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ') }
    'readable' { (Get-Date).ToString('MMMM d, yyyy') }
    'short' { (Get-Date).ToString('MMM d, yyyy') }
    'timestamp' { (Get-Date).ToString('yyyyMMdd_HHmmss') }
    default { Write-Error "Unknown: $Format"; exit 1 }
}


