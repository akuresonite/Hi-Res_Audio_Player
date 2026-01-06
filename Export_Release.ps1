# =================================================
# 🔖 Release Version (CHANGE ONLY THIS LINE)
# =================================================
$VERSION = "1.0.0"
# =================================================

$ErrorActionPreference = "Stop"

# -----------------------------
# Deactivate conda if active
# -----------------------------
if (Test-Path env:CONDA_PREFIX) {
    conda deactivate
}

# -----------------------------
# Activate virtual environment
# -----------------------------
$venvScript = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $venvScript
}
else {
    Write-Warning "Virtual environment script not found at $venvScript"
}

# -----------------------------
# Build APK
# -----------------------------
Write-Host "Starting build process..." -ForegroundColor Green
flet build apk
Write-Host "Build completed." -ForegroundColor Cyan

# -----------------------------
# Locate APK & SHA1
# -----------------------------
$BuildDir = Join-Path $PSScriptRoot "build\apk"

$ApkFile = Get-ChildItem $BuildDir -Filter *.apk | Select-Object -First 1
$Sha1File = Get-ChildItem $BuildDir -Filter *.sha1 | Select-Object -First 1

if (-not $ApkFile) {
    Write-Error "❌ APK not found in $BuildDir"
}

if (-not $Sha1File) {
    Write-Error "❌ SHA1 file not found in $BuildDir"
}

Write-Host "Found APK: $($ApkFile.Name)" -ForegroundColor Green
Write-Host "Found SHA1: $($Sha1File.Name)" -ForegroundColor Green

# -----------------------------
# Git & GH pre-checks
# -----------------------------
git rev-parse --is-inside-work-tree | Out-Null
gh auth status | Out-Null

# -----------------------------
# Create & push tag
# -----------------------------
$TAG = "v$VERSION"

git tag $TAG
git push origin $TAG

# -----------------------------
# Create GitHub Release
# -----------------------------
gh release create $TAG `
    $ApkFile.FullName `
    $Sha1File.FullName `
    --title "v$VERSION" `
    --notes "Release v$VERSION"

Write-Host "✅ GitHub Release v$VERSION created successfully!" -ForegroundColor Green
    