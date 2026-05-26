param(
  [string]$HostName = $(if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }),
  [int]$Port = $(if ($env:API_PORT) { [int]$env:API_PORT } else { 8000 })
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"

function Get-UsablePython {
  if (Test-Path $VenvPython) {
    return $VenvPython
  }

  $commands = Get-Command python -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -and $_.Source -notlike "*\Microsoft\WindowsApps\*" }

  if ($commands) {
    return $commands[0].Source
  }

  $pyCommands = Get-Command py -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -and $_.Source -notlike "*\Microsoft\WindowsApps\*" }

  if ($pyCommands) {
    return $pyCommands[0].Source
  }

  $localPythonRoots = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
  )

  foreach ($candidate in $localPythonRoots) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw "Python is not installed or only the broken Windows Store alias is available. Install Python 3.11+ and reopen the terminal."
}

$Python = Get-UsablePython

Write-Host "Starting FastAPI on http://${HostName}:${Port}"
& $Python -m uvicorn app.main:app --app-dir apps/api --reload --host $HostName --port $Port
