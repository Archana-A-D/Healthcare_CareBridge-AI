param(
  [Parameter(Mandatory = $true)]
  [string]$SummaryId,
  [int]$Users = 3,
  [int]$Minutes = 2,
  [int]$SpawnRate = 1,
  [int]$QueryLimitPerUser = 1,
  [int]$BackendPort = 8000
)

$ErrorActionPreference = 'Stop'
if ($Users -lt 1 -or $Minutes -lt 1 -or $SpawnRate -lt 1 -or $QueryLimitPerUser -lt 0) {
  throw 'Users, Minutes, and SpawnRate must be positive integers; QueryLimitPerUser may be zero.'
}

$env:BACKEND_PORT = "$BackendPort"
$env:LOAD_TEST_SUMMARY_ID = $SummaryId
$env:LOAD_TEST_ASYNC = '1'
$env:LOAD_TEST_QUERY_LIMIT_PER_USER = "$QueryLimitPerUser"
$prefix = "/results/query-$Users-users"
$sha = [Security.Cryptography.SHA256]::Create()
$summaryHash = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($SummaryId)))).Replace('-', '').ToLowerInvariant()
$sha.Dispose()
$backendEnv = @{}
if (Test-Path -LiteralPath 'backend/.env') {
  Get-Content -LiteralPath 'backend/.env' | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
      $parts = $line -split '=', 2
      $backendEnv[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
  }
}
$profile = @{
  users = $Users
  duration = "${Minutes}m"
  spawn_rate = $SpawnRate
  ai_mode = 'Gemini async'
  ai_model = $(if ($backendEnv.ContainsKey('GEMINI_MODEL')) { $backendEnv['GEMINI_MODEL'] } else { 'default' })
  prompt_version = $(if ($backendEnv.ContainsKey('CAREBRIDGE_PROMPT_VERSION')) { $backendEnv['CAREBRIDGE_PROMPT_VERSION'] } else { 'v3' })
  environment = "$env:COMPUTERNAME; Docker Compose"
  data_sha256 = $summaryHash
  warmup_requests = 0
  query_limit_per_user = $QueryLimitPerUser
}
$profile | ConvertTo-Json | Set-Content -LiteralPath "loadtest/results/query-$Users-users-profile.json" -Encoding ascii
Write-Warning "Each virtual user can submit at most $QueryLimitPerUser Gemini document question(s). This can use API quota and incur cost."
Write-Host 'Ensure the backend, Redis, MySQL, and Celery worker are running in this Compose project.'
docker compose --profile loadtest run --rm -T locust `
  -f /loadtest/locustfile.py `
  --headless `
  --host http://backend:8000 `
  --users $Users `
  --spawn-rate $SpawnRate `
  --run-time "${Minutes}m" `
  --csv $prefix
if ($LASTEXITCODE -ne 0) {
  throw 'Locust reported failed requests. Inspect loadtest/results/*_failures.csv.'
}
