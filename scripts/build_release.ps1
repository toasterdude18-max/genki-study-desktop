<#
Build a release of the Genki Study desktop app:
  1. stamp the version into app\models.py
  2. rebuild the onedir bundle into release\
  3. compile the Inno Setup installer
  4. compute the SHA-256 checksum
  5. update the web project's download page (version + hash)
Usage:  .\scripts\build_release.ps1 [-Version 1.0.1]
#>
param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$iscc = "C:\Users\tiger\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
$webRoot = "C:\Users\tiger\genki-study-app\pagelove"

Write-Host "=== 1/5 stamp version $Version into models.py ==="
$mp = Join-Path $root "app\models.py"
(Get-Content $mp -Raw) -replace 'VERSION = "[^"]*"', "VERSION = `"$Version`"" |
    Set-Content $mp -NoNewline -Encoding UTF8

Write-Host "=== 2/5 rebuild onedir bundle ==="
Remove-Item (Join-Path $root "release") -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $root "release") | Out-Null
python -m PyInstaller --noconfirm --onedir --windowed --name "Genki Study" `
    --icon (Join-Path $root "assets\genki.ico") --collect-all pyttsx3 `
    --distpath (Join-Path $root "release") `
    --workpath (Join-Path $root "build") `
    --specpath (Join-Path $root "build") `
    app\main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "=== 3/5 bundle content data ==="
New-Item -ItemType Directory -Force -Path (Join-Path $root "release\Genki Study\data") | Out-Null
Copy-Item (Join-Path $root "data\genki-data.json") `
          (Join-Path $root "release\Genki Study\data\genki-data.json") -Force

Write-Host "=== 4/5 compile installer ==="
& $iscc "/DMyAppVersion=$Version" (Join-Path $root "installer\genki_study.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

$setup = Join-Path $root "release\Genki-Study-Setup-v$Version.exe"
if (-not (Test-Path $setup)) { throw "Installer not found at $setup" }

Write-Host "=== 5/5 checksum + web page update ==="
$hash = (Get-FileHash $setup -Algorithm SHA256).Hash.ToLower()
$sizeMB = [math]::Round((Get-Item $setup).Length / 1MB, 1)
"Genki-Study-Setup-v$Version.exe`tSHA256: $hash`t$sizeMB MB" |
    Out-File (Join-Path $root "release\checksums.txt") -Encoding ascii

$dl = Join-Path $webRoot "download.html"
if (Test-Path $dl) {
    $html = Get-Content $dl -Raw
    $assetUrl = "https://github.com/toasterdude18-max/genki-study-desktop/releases/latest/download/Genki-Study-Setup-v$Version.exe"
    $html = $html -replace 'id="dl-version">[^<]*<', "id=`"dl-version`">$Version<"
    $html = $html -replace 'id="dl-version2">[^<]*<', "id=`"dl-version2`">$Version<"
    $html = $html -replace 'id="dl-hash">[^<]*<', "id=`"dl-hash`">$hash<"
    $html = $html -replace 'id="dl-size">[^<]*<', "id=`"dl-size`">$sizeMB MB<"
    $html = $html -replace 'id="dl-url" href="[^"]*"', "id=`"dl-url`" href=`"$assetUrl`""
    Set-Content $dl $html -NoNewline -Encoding UTF8
    Write-Host "updated $dl"
}

Write-Host ""
Write-Host "RELEASE READY: $setup"
Write-Host "SHA256: $hash"
Write-Host "Next: gh release create v$Version `"$setup`" `"$(Join-Path $root 'release\checksums.txt')`" --notes `"SHA-256: $hash`""
