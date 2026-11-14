param(
    [switch]$Tuning,
    [switch]$All,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path $PSScriptRoot -Parent
$venvPython = Join-Path $projectRoot ".venv/Scripts/python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
$runId = "$(Get-Date -Format yyyyMMdd-HHmmss)-$PID-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
$runRoot = Join-Path $projectRoot ".pytest_tmp/$runId"

$explicitTargets = @(
    $PytestArgs | Where-Object {
        $_ -and -not $_.StartsWith("-") -and (Test-Path -LiteralPath (Join-Path $projectRoot (($_ -split "::")[0])))
    }
)
$marker = if ($Tuning) { "tuning" } elseif ($All -or $explicitTargets.Count -gt 0) { "" } else { "not tuning" }
$markerArgs = if ($marker) { @("-m", $marker) } else { @() }

Push-Location $projectRoot

try {
    New-Item -ItemType Directory -Force -Path ".pytest_tmp" | Out-Null
    New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

    & $python -m pytest @markerArgs @PytestArgs `
        --basetemp="$runRoot/tmp" `
        -o "cache_dir=$runRoot/cache"

    $pytestExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $runRoot) {
        Remove-Item -LiteralPath $runRoot -Recurse -Force
    }
}

exit $pytestExitCode
