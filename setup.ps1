param(
    [string]$VenvDir = (Join-Path $PSScriptRoot ".venv")
)

Write-Host "==> Kase Agent Setup" -ForegroundColor Cyan
Write-Host "    Venv: $VenvDir"

$Python = if (Get-Command "python" -ErrorAction SilentlyContinue) { "python" }
           elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" }
           else { throw "Python not found. Install Python 3.11+" }

# Check if externally managed (Windows typically isn't, but support flag)
$ExternallyManaged = $false
try {
    $result = & $Python -c "import sysconfig; v=sysconfig.get_config_var('EXTERNALLY_MANAGED'); print(v or '')" 2>&1
    if ($result -match "1") { $ExternallyManaged = $true }
} catch {}

if ($ExternallyManaged -and !(Test-Path $VenvDir)) {
    Write-Host "==> Creating virtual environment..." -ForegroundColor Cyan
    & $Python -m venv $VenvDir
    $Pip = (Join-Path $VenvDir "Scripts\pip.exe")
    $Python = Join-Path $VenvDir "Scripts\python.exe"
    Write-Host "    Activate with: $VenvDir\Scripts\Activate.ps1" -ForegroundColor Yellow
} else {
    $Pip = "pip"
}

Write-Host "==> Installing Kase Agent..." -ForegroundColor Cyan
& $Pip install --upgrade pip
& $Pip install -e $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Kase Agent installed successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Quick start:" -ForegroundColor Cyan
Write-Host "    `$env:OPENAI_API_KEY = `"sk-...`""
Write-Host "    kase"
if ($ExternallyManaged) {
    Write-Host ""
    Write-Host "  Remember to activate the venv:" -ForegroundColor Yellow
    Write-Host "    $VenvDir\Scripts\Activate.ps1" -ForegroundColor Yellow
}
