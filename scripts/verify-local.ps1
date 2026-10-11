param([string]$DockerExecutable)

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Error 'Python virtual environment is missing. Create .venv and install the locked project dependencies first.'
    exit 1
}

Push-Location $repoRoot
try {
    $arguments = @('-m', 'scripts.local_infra', 'verify')
    if ($DockerExecutable) { $arguments += @('--docker-executable', $DockerExecutable) }
    & $python @arguments
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
