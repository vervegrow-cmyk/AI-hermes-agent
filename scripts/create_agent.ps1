param(
    [Parameter(Mandatory = $true)]
    [string]$AgentName,
    [string]$Template = "python-fastapi-agent"
)

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "templates/$Template"
$target = Join-Path $root "agents/$AgentName"

if (-not (Test-Path $source)) {
    throw "Template not found: $Template"
}

if (Test-Path $target) {
    throw "Target already exists: $target"
}

Copy-Item -Path $source -Destination $target -Recurse
Write-Host "Created agent scaffold at $target"

