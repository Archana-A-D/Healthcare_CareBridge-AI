param(
  [int]$ShortUsers = 3,
  [int]$ShortMinutes = 2,
  [int]$LoadUsers = 10,
  [int]$LoadMinutes = 5,
  [int]$SpawnRate = 2,
  [int]$BackendPort = 8000
)

$ErrorActionPreference = 'Stop'
$profiles = @(
  @{ Name = 'syllabus-3-users'; Users = $ShortUsers; Minutes = $ShortMinutes },
  @{ Name = 'syllabus-10-users'; Users = $LoadUsers; Minutes = $LoadMinutes }
)

foreach ($profile in $profiles) {
  Write-Host "Running $($profile.Name): $($profile.Users) users, ${SpawnRate}/s ramp, $($profile.Minutes)m."
  # Warm Redis and each Gunicorn worker's database connection so cold boot
  # is measured separately from steady-state concurrent latency.
  1..6 | ForEach-Object {
    Invoke-RestMethod "http://127.0.0.1:$BackendPort/api/health/" | Out-Null
    Invoke-RestMethod "http://127.0.0.1:$BackendPort/api/agent/usage/" | Out-Null
  }
  docker compose --profile loadtest run --rm -T locust `
    -f /loadtest/locustfile.py `
    --headless `
    --host http://backend:8000 `
    --users $profile.Users `
    --spawn-rate $SpawnRate `
    --run-time "$($profile.Minutes)m" `
    --csv "/results/$($profile.Name)"
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "$($profile.Name) reported request failures; inspect the generated _failures.csv and Locust output."
  }
}

Write-Host 'These profiles use the locustfile default health/usage traffic unless LOAD_TEST_SUMMARY_ID is set.'
Write-Host 'Health/usage-only results do not establish AI answer latency or accuracy.'
