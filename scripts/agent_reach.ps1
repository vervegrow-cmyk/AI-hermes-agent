$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$agentReachRoot = Join-Path $repoRoot "external\Agent-Reach"
$venvScripts = Join-Path $agentReachRoot ".venv-agent-reach\Scripts"
$agentReachExe = Join-Path $venvScripts "agent-reach.exe"

if (-not (Test-Path $agentReachExe)) {
    throw "Agent Reach CLI not found: $agentReachExe"
}

$env:PATH = "$venvScripts;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"

Push-Location $agentReachRoot
try {
    & $agentReachExe @args
}
finally {
    Pop-Location
}
