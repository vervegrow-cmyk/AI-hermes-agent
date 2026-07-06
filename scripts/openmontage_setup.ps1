[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$script:OpenMontageSetupMessages = @{
    missing_dir = "W09wZW5Nb250YWdlIFNldHVwXSDmnKrmib7liLAgT3Blbk1vbnRhZ2Ug55uu5b2VOiB7MH0="
    missing_python = "W09wZW5Nb250YWdlIFNldHVwXSDnvLrlsJEgUHl0aG9u77yM6K+35YWI5a6J6KOFIFB5dGhvbiAzLjEwK+OAgg=="
    missing_node = "W09wZW5Nb250YWdlIFNldHVwXSDnvLrlsJEgTm9kZS5qc++8jOivt+WFiOWuieijhSBOb2RlLmpzIDE4K+OAgg=="
    missing_ffmpeg = "T3Blbk1vbnRhZ2Ug6ZyA6KaBIEZGbXBlZ++8jOivt+WuieijheWQjumHjeaWsOi/kOihjCBzZXR1cOOAgg=="
    python_version = "UHl0aG9uIOeJiOacrDogezB9"
    node_version = "Tm9kZS5qcyDniYjmnKw6IHswfQ=="
    ffmpeg_ok = "RkZtcGVnIOW3suWPr+eUqA=="
    install_py = "5a6J6KOFIE9wZW5Nb250YWdlIFB5dGhvbiByZXF1aXJlbWVudHM="
    install_npm = "5a6J6KOFIHJlbW90aW9uLWNvbXBvc2VyIG5wbSDkvp3otZY="
    done = "W09wZW5Nb250YWdlIFNldHVwXSDlronoo4XlrozmiJDjgII="
}

function Get-OpenMontageSetupMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key,

        [object[]]$Args = @()
    )

    $template = [System.Text.Encoding]::UTF8.GetString(
        [System.Convert]::FromBase64String($script:OpenMontageSetupMessages[$Key])
    )

    if ($Args.Count -gt 0) {
        return [string]::Format($template, $Args)
    }

    return $template
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir "openmontage_env.ps1")

$repoRoot = Split-Path -Parent $scriptDir
$openMontagePath = Join-Path $repoRoot "external\OpenMontage"
$remotionPath = Join-Path $openMontagePath "remotion-composer"

function Test-CommandAvailable {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Action
    )

    Write-Host "[OpenMontage Setup] $Message"
    & $Action
}

if (-not (Test-Path -LiteralPath $openMontagePath)) {
    Write-Host (Get-OpenMontageSetupMessage -Key "missing_dir" -Args @($openMontagePath))
    exit 1
}

if (-not (Test-CommandAvailable "python")) {
    Write-Host (Get-OpenMontageSetupMessage -Key "missing_python")
    exit 1
}

if (-not (Test-CommandAvailable "node")) {
    Write-Host (Get-OpenMontageSetupMessage -Key "missing_node")
    exit 1
}

if (-not (Test-CommandAvailable "ffmpeg")) {
    Write-Host (Get-OpenMontageSetupMessage -Key "missing_ffmpeg")
    exit 1
}

Invoke-Step -Message (Get-OpenMontageSetupMessage -Key "python_version" -Args @((python --version))) -Action { $null = $true }
Invoke-Step -Message (Get-OpenMontageSetupMessage -Key "node_version" -Args @((node -v))) -Action { $null = $true }
Invoke-Step -Message (Get-OpenMontageSetupMessage -Key "ffmpeg_ok") -Action { $null = $true }

Invoke-Step -Message (Get-OpenMontageSetupMessage -Key "install_py") -Action {
    Set-Location $openMontagePath
    python -m pip install -r requirements.txt
}

Invoke-Step -Message (Get-OpenMontageSetupMessage -Key "install_npm") -Action {
    Set-Location $remotionPath
    npx --yes npm install
}

Write-Host (Get-OpenMontageSetupMessage -Key "done")
