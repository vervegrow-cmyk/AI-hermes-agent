[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$script:OpenMontageEnvMessages = @{
    env_loaded = "W09wZW5Nb250YWdl546v5aKDXSDlt7LliqDovb3kuIrlsYLnjq/looPlj5jph48="
    env_path = "W09wZW5Nb250YWdl546v5aKDXSBPcGVuTW9udGFnZei3r+W+hD17MH0="
}

function Get-OpenMontageEnvMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key,

        [object[]]$Args = @()
    )

    $template = [System.Text.Encoding]::UTF8.GetString(
        [System.Convert]::FromBase64String($script:OpenMontageEnvMessages[$Key])
    )

    if ($Args.Count -gt 0) {
        return [string]::Format($template, $Args)
    }

    return $template
}

function Import-DotEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $match = [regex]::Match($line, '^(?<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?<value>.*)$')
        if (-not $match.Success) {
            return
        }

        $key = $match.Groups["key"].Value
        $value = $match.Groups["value"].Value.Trim()

        if ($value.Length -ge 2) {
            $startsWithDouble = $value.StartsWith('"')
            $endsWithDouble = $value.EndsWith('"')
            $startsWithSingle = $value.StartsWith("'")
            $endsWithSingle = $value.EndsWith("'")
            if (($startsWithDouble -and $endsWithDouble) -or ($startsWithSingle -and $endsWithSingle)) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }

        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$openMontagePath = Join-Path $repoRoot "external\OpenMontage"

Import-DotEnvFile -Path (Join-Path $repoRoot ".env")
Import-DotEnvFile -Path (Join-Path $openMontagePath ".env")
Import-DotEnvFile -Path (Join-Path $openMontagePath ".env.local")

$env:AI_HERMES_ROOT = $repoRoot
$env:OPENMONTAGE_PATH = $openMontagePath

Write-Host (Get-OpenMontageEnvMessage -Key "env_loaded")
Write-Host (Get-OpenMontageEnvMessage -Key "env_path" -Args @($openMontagePath))
