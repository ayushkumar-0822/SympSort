Write-Host "Starting SympSort..." -ForegroundColor Cyan
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $PSScriptRoot "main.py") @args
} else {
    python (Join-Path $PSScriptRoot "main.py") @args
}
