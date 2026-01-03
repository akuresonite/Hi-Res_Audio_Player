$ErrorActionPreference = "Stop"

# Deactivate conda if it's active
if (Test-Path env:CONDA_PREFIX) {
    conda deactivate
}

# Activate the local virtual environment
$venvScript = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $venvScript
}
else {
    Write-Warning "Virtual environment script not found at $venvScript"
}

# Run the build command
Write-Host "Starting build process..." -ForegroundColor Green
flet build apk
Write-Host "Build command executed." -ForegroundColor Cyan

# Copy the build output to the project root
$sourcePath = "D:\Ashish\Google Drive Laptop\projects\Mobile-Apps\Hi-Res_Audio_Player\build\apk"
$destPath = "D:\Ashish\Google Drive Laptop\projects\Mobile-Apps\Hi-Res_Audio_Player"

if (Test-Path $sourcePath) {
    Write-Host "Copying APK folder to project root..." -ForegroundColor Green
    Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
}
else {
    Write-Warning "Source folder not found: $sourcePath"
}
