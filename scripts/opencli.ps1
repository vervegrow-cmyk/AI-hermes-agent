$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$opencliRoot = Join-Path $repoRoot "external\OpenCLI"
$opencliCmd = Join-Path $opencliRoot "node_modules\.bin\opencli.cmd"
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

if (-not (Test-Path $opencliCmd)) {
    throw "OpenCLI executable not found: $opencliCmd"
}

Import-DotEnv -Path $rootEnvFile

$env:PATH = "$opencliRoot\node_modules\.bin;$env:PATH"
$env:OPENCLI_ROOT = $opencliRoot
$env:PYTHONIOENCODING = "utf-8"

Push-Location $opencliRoot
try {
    & $opencliCmd @args
}
finally {
    Pop-Location
}
