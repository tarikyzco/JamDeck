# JamDeck surum paketi: pyinstaller build + release zip
# Kullanim: backend\version.py icindeki APP_VERSION'i yukselt, sonra .\build_release.ps1
# Cikti: release\JamDeck-v{X}-win64.zip  (zip koku "Ayazjam Manager\" klasoru —
# uygulamadaki guncelleyicinin stage_zip() fonksiyonunun bekledigi yapi)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# 1) surumu tek kaynaktan oku
$verLine = Select-String -Path "backend\version.py" -Pattern 'APP_VERSION\s*=\s*"([^"]+)"'
if (-not $verLine) { Write-Error "backend\version.py icinde APP_VERSION bulunamadi"; exit 1 }
$ver = $verLine.Matches[0].Groups[1].Value
Write-Host "JamDeck v$ver paketleniyor..." -ForegroundColor Cyan

# 2) temiz build
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
pyinstaller "Ayazjam Manager.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller basarisiz (exit $LASTEXITCODE)"; exit 1 }
if (-not (Test-Path "dist\Ayazjam Manager\Ayazjam Manager.exe")) {
    Write-Error "dist\Ayazjam Manager\Ayazjam Manager.exe uretilmedi"; exit 1
}

# 3) zip (kok klasor dahil) — guncelleyicinin indirdigi asset BU; her release'te sart
if (-not (Test-Path "release")) { New-Item -ItemType Directory "release" | Out-Null }
$zip = "release\JamDeck-v$ver-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "dist\Ayazjam Manager" -DestinationPath $zip
Write-Host "Hazir: $zip" -ForegroundColor Green

# 4) kurulum exe'si (Inno Setup) — ilk kurulum icin onerilen dagitim
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "/DMyAppVersion=$ver" "installer.iss" /Q
    if ($LASTEXITCODE -ne 0) { Write-Error "Inno Setup derlemesi basarisiz"; exit 1 }
    Write-Host "Hazir: release\JamDeck-Setup-v$ver.exe" -ForegroundColor Green
} else {
    Write-Warning "Inno Setup bulunamadi - kurulum exe'si atlandi (winget install JRSoftware.InnoSetup)"
}

Write-Host "Yayinlamak icin:" -ForegroundColor Yellow
Write-Host "  gh release create v$ver `"$zip`" `"release\JamDeck-Setup-v$ver.exe`" --title `"v$ver`" --notes-file notlar.md" -ForegroundColor Yellow
