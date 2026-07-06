[CmdletBinding()]
param(
    [string[]]$Keys = @(),

    [switch]$LoadEnv
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-DotEnvKeys {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $result = @{}

    if (-not (Test-Path -LiteralPath $Path)) {
        return $result
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $match = [regex]::Match($line, '^(?<key>[A-Za-z_][A-Za-z0-9_]*)\s*=')
        if ($match.Success) {
            $result[$match.Groups["key"].Value] = $true
        }
    }

    return $result
}

function Get-Checkmark {
    param([bool]$Value)

    if ($Value) {
        return "Y"
    }

    return "N"
}

$repoRoot = Get-RepoRoot
$openMontagePath = Join-Path $repoRoot "external\OpenMontage"
$rootEnvPath = Join-Path $repoRoot ".env"
$openMontageEnvPath = Join-Path $openMontagePath ".env"
$openMontageLocalEnvPath = Join-Path $openMontagePath ".env.local"

if ($LoadEnv) {
    . (Join-Path $repoRoot "scripts\openmontage_env.ps1")
}

$rootEnvKeys = Get-DotEnvKeys -Path $rootEnvPath
$openMontageEnvKeys = Get-DotEnvKeys -Path $openMontageEnvPath
$openMontageLocalEnvKeys = Get-DotEnvKeys -Path $openMontageLocalEnvPath

if ($Keys.Count -eq 0) {
    $allKeys = @(
        $rootEnvKeys.Keys +
        $openMontageEnvKeys.Keys +
        $openMontageLocalEnvKeys.Keys
    ) | Sort-Object -Unique
}
else {
    $allKeys = @(
        $Keys | ForEach-Object {
            $_ -split "," | ForEach-Object { $_.Trim() }
        }
    ) | Where-Object { $_ } | Sort-Object -Unique
}

if ($allKeys.Count -eq 0) {
    Write-Host "[OpenMontage Env Check] No keys found to inspect."
    Write-Host "[OpenMontage Env Check] Pass -Keys or make sure the root .env exists."
    exit 1
}

Write-Host "[OpenMontage Env Check] RepoRoot=$repoRoot"
Write-Host "[OpenMontage Env Check] OpenMontagePath=$openMontagePath"
Write-Host "[OpenMontage Env Check] Only presence/load status is shown. Secret values are never printed."
if (-not $LoadEnv) {
    Write-Host "[OpenMontage Env Check] .env was not auto-loaded in this run. Add -LoadEnv if needed."
}

$rows = foreach ($key in $allKeys) {
    $inRootEnv = $rootEnvKeys.ContainsKey($key)
    $inOpenMontageEnv = $openMontageEnvKeys.ContainsKey($key)
    $inOpenMontageLocalEnv = $openMontageLocalEnvKeys.ContainsKey($key)
    $inProcess = -not [string]::IsNullOrEmpty([System.Environment]::GetEnvironmentVariable($key, "Process"))

    [PSCustomObject]@{
        Key                 = $key
        RootEnv             = Get-Checkmark $inRootEnv
        OpenMontageEnv      = Get-Checkmark $inOpenMontageEnv
        OpenMontageEnvLocal = Get-Checkmark $inOpenMontageLocalEnv
        CurrentSession      = Get-Checkmark $inProcess
    }
}

$rows | Format-Table -AutoSize

$loadedCount = @($rows | Where-Object { $_.CurrentSession -eq "Y" }).Count
$missingCount = @($rows | Where-Object { $_.CurrentSession -eq "N" }).Count

Write-Host "[OpenMontage Env Check] Loaded in current session: $loadedCount key(s)."
if ($missingCount -gt 0) {
    Write-Host "[OpenMontage Env Check] Missing in current session: $missingCount key(s)."
}

Write-Host "[OpenMontage Env Check] Example 1:"
Write-Host 'powershell -ExecutionPolicy Bypass -File .\scripts\openmontage_env_check.ps1 -Keys OPENAI_API_KEY,FAL_KEY -LoadEnv'
Write-Host "[OpenMontage Env Check] Example 2 (inspect the current PowerShell session):"
Write-Host '. .\scripts\openmontage_env.ps1'
Write-Host '. .\scripts\openmontage_env_check.ps1 -Keys OPENAI_API_KEY,FAL_KEY'
