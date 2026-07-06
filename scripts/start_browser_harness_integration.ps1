$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$openhandsRoot = Join-Path $repoRoot "external\OpenHands"
$browserHarnessServer = Join-Path $repoRoot "tools\mcp\browser_harness_mcp_server.py"

function Start-BrowserHarnessMcp {
    $existing = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -like '*browser_harness_mcp_server.py*' -and $_.ProcessId -ne $PID
    }

    if ($existing) {
        return [int]$existing[0].ProcessId
    }

    $command = "`$env:HERMES_MCP_TRANSPORT='http'; `$env:HERMES_MCP_PORT='8094'; Set-Location '$repoRoot'; python '$browserHarnessServer'"
    $proc = Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile', '-WindowStyle', 'Hidden', '-Command', $command -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 3
    return [int]$proc.Id
}

function Ensure-DockerDesktop {
    try {
        docker version | Out-Null
        return $true
    }
    catch {
        Start-Service com.docker.service -ErrorAction SilentlyContinue
        Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden

        for ($i = 0; $i -lt 18; $i++) {
            Start-Sleep -Seconds 5
            try {
                docker version | Out-Null
                return $true
            }
            catch {
            }
        }
    }

    return $false
}

function Start-OpenHands {
    if (-not (Test-Path $openhandsRoot)) {
        return $false
    }

    $env:OPENHANDS_HOST_PORT = '3002'
    $env:WORKSPACE_BASE = $repoRoot
    $env:PWD = $openhandsRoot
    $env:DATE = Get-Date -Format 'yyyyMMddHHmmss'

    Push-Location $openhandsRoot
    try {
        docker compose up -d | Out-Null
    }
    finally {
        Pop-Location
    }

    for ($i = 0; $i -lt 18; $i++) {
        Start-Sleep -Seconds 5
        try {
            $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:3002/' -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
        }
    }

    return $false
}

$mcpPid = Start-BrowserHarnessMcp
$dockerReady = Ensure-DockerDesktop
$openhandsReady = $false
$registered = $false

if ($dockerReady) {
    $openhandsReady = Start-OpenHands
    if ($openhandsReady) {
        Push-Location $repoRoot
        try {
            python .\scripts\register_openhands_browser_harness_mcp.py | Out-Null
            $registered = $true
        }
        finally {
            Pop-Location
        }
    }
}

[pscustomobject]@{
    browser_harness_mcp_pid = $mcpPid
    docker_ready = $dockerReady
    openhands_ready = $openhandsReady
    browser_harness_registered_in_openhands = $registered
} | ConvertTo-Json -Compress
