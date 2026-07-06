$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$repoRoot = Split-Path -Parent $PSScriptRoot
$browserHarnessRoot = Join-Path $repoRoot "external\browser-harness"
$defaultExe = Join-Path $env:USERPROFILE ".local\bin\browser-harness.exe"
$browserHarnessExe = if ($env:BROWSER_HARNESS_EXE) { $env:BROWSER_HARNESS_EXE } else { $defaultExe }
$rootEnvFile = Join-Path $repoRoot ".env"

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $separatorIndex = $trimmed.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }

        $name = $trimmed.Substring(0, $separatorIndex).Trim()
        $value = $trimmed.Substring($separatorIndex + 1)

        if (
            ($value.Length -ge 2) -and
            (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))
            )
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        if (-not (Test-Path "Env:$name")) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

if (-not (Test-Path $browserHarnessRoot)) {
    New-Item -ItemType Directory -Path $browserHarnessRoot -Force | Out-Null
}

Import-DotEnv -Path $rootEnvFile

if (-not (Test-Path $browserHarnessExe)) {
    throw "browser-harness executable not found: $browserHarnessExe"
}

$env:PATH = "$(Split-Path -Parent $browserHarnessExe);$env:PATH"
$env:BROWSER_HARNESS_ROOT = $browserHarnessRoot
$env:BROWSER_HARNESS_EXE = $browserHarnessExe
$env:BH_AGENT_WORKSPACE = $repoRoot

Push-Location $browserHarnessRoot
try {
    $stdinText = ""
    try {
        if ([Console]::IsInputRedirected) {
            $stdinText = [Console]::In.ReadToEnd()
        }
    }
    catch {
    }

    if ($stdinText) {
        $stdinText | & $browserHarnessExe @args
    }
    else {
        & $browserHarnessExe @args
    }
}
finally {
    Pop-Location
}
