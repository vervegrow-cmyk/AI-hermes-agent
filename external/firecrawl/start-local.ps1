$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sharedEnvPath = Join-Path $repoRoot ".env"
$firecrawlEnvPath = Join-Path $PSScriptRoot ".env.local-runtime"

function Import-EnvFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $pair = $line -split "=", 2
        if ($pair.Count -ne 2) {
            return
        }

        [System.Environment]::SetEnvironmentVariable($pair[0], $pair[1], "Process")
    }
}

Import-EnvFile -Path $sharedEnvPath
Import-EnvFile -Path $firecrawlEnvPath

Write-Host "Using shared env:" $sharedEnvPath
Write-Host "Using firecrawl env:" $firecrawlEnvPath

Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\playwright-service-ts'; pnpm run dev" -WindowStyle Normal
Start-Sleep -Seconds 5
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\api'; pnpm run dev" -WindowStyle Normal
