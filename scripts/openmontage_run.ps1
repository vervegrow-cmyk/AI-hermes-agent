[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$job_file,

    [Parameter(Mandatory = $true)]
    [string]$output_dir,

    [string]$mode = "job"
)

$ErrorActionPreference = "Stop"

$script:OpenMontageRunMessages = @{
    missing_dir = "W09wZW5Nb250YWdlIFJ1bl0g5pyq5om+5YiwIE9wZW5Nb250YWdlIOebruW9lTogezB9"
    missing_job = "W09wZW5Nb250YWdlIFJ1bl0g5pyq5om+5YiwIGpvYl9maWxlOiB7MH0="
    mode = "W09wZW5Nb250YWdlIFJ1bl0g5qih5byPPXswfQ=="
    job_file = "W09wZW5Nb250YWdlIFJ1bl0gam9iX2ZpbGU9ezB9"
    output_dir = "W09wZW5Nb250YWdlIFJ1bl0gb3V0cHV0X2Rpcj17MH0="
    run_path = "W09wZW5Nb250YWdlIFJ1bl0gT3Blbk1vbnRhZ2Xot6/lvoQ9ezB9"
    demo_detected = "W09wZW5Nb250YWdlIFJ1bl0g5qOA5rWL5YiwIHJlbmRlcl9kZW1vLnB577yM5bCG5omn6KGMIFJFQURNRSDkuK3nmoQgZGVtbyDmuLLmn5Plkb3ku6TjgII="
    demo_done = "W09wZW5Nb250YWdlIFJ1bl0gRGVtbyDmiafooYzlrozmiJDjgII="
    demo_fail = "W09wZW5Nb250YWdlIFJ1bl0gRGVtbyDmiafooYzlpLHotKU6IHswfQ=="
    log_path = "W09wZW5Nb250YWdlIFJ1bl0g5pel5b+X6Lev5b6EPXswfQ=="
    no_cli = "W09wZW5Nb250YWdlIFJ1bl0g5b2T5YmN5LuT5bqT5pyq5Y+R546w56iz5a6a55qE6YCa55SoIENMSe+8jOacquS8qumAoOaJp+ihjOWRveS7pOOAgg=="
    job_created = "W09wZW5Nb250YWdlIFJ1bl0g5bey55Sf5oiQIGpvYl9maWxl44CC"
    codex_instruction = "W09wZW5Nb250YWdlIFJ1bl0g6K+3IENvZGV4IOWcqCBleHRlcm5hbC9PcGVuTW9udGFnZSDkuK3or7vlj5YgQUdFTlRfR1VJREUubWQg5ZCO5omn6KGMIGpvYl9maWxl44CC"
}

function Get-OpenMontageRunMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key,

        [object[]]$Args = @()
    )

    $template = [System.Text.Encoding]::UTF8.GetString(
        [System.Convert]::FromBase64String($script:OpenMontageRunMessages[$Key])
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
$logsDir = Join-Path $repoRoot "runtime\logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logsDir ("openmontage_run_{0}.log" -f $timestamp)

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $output_dir | Out-Null

function Write-RunLog {
    param([string]$Message)
    $Message | Tee-Object -FilePath $logPath -Append
}

if (-not (Test-Path -LiteralPath $openMontagePath)) {
    Write-RunLog (Get-OpenMontageRunMessage -Key "missing_dir" -Args @($openMontagePath))
    exit 1
}

if (-not (Test-Path -LiteralPath $job_file)) {
    Write-RunLog (Get-OpenMontageRunMessage -Key "missing_job" -Args @($job_file))
    exit 1
}

Set-Location $openMontagePath
$demoScriptPath = Join-Path $openMontagePath "render_demo.py"

Write-RunLog (Get-OpenMontageRunMessage -Key "mode" -Args @($mode))
Write-RunLog (Get-OpenMontageRunMessage -Key "job_file" -Args @($job_file))
Write-RunLog (Get-OpenMontageRunMessage -Key "output_dir" -Args @($output_dir))
Write-RunLog (Get-OpenMontageRunMessage -Key "run_path" -Args @($openMontagePath))

if ($mode -eq "demo" -and (Test-Path -LiteralPath $demoScriptPath)) {
    Write-RunLog (Get-OpenMontageRunMessage -Key "demo_detected")
    try {
        python $demoScriptPath 2>&1 | Tee-Object -FilePath $logPath -Append
        Write-RunLog (Get-OpenMontageRunMessage -Key "demo_done")
        Write-RunLog (Get-OpenMontageRunMessage -Key "log_path" -Args @($logPath))
        exit 0
    }
    catch {
        Write-RunLog (Get-OpenMontageRunMessage -Key "demo_fail" -Args @($_.Exception.Message))
        Write-RunLog (Get-OpenMontageRunMessage -Key "log_path" -Args @($logPath))
        exit 1
    }
}

Write-RunLog (Get-OpenMontageRunMessage -Key "no_cli")
Write-RunLog (Get-OpenMontageRunMessage -Key "job_created")
Write-RunLog (Get-OpenMontageRunMessage -Key "codex_instruction")
Write-RunLog (Get-OpenMontageRunMessage -Key "log_path" -Args @($logPath))
