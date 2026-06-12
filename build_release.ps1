# JamDeck surum paketi: pyinstaller build + release zip + kurulum exe'si
# Kullanim: backend\version.py icindeki APP_VERSION'i yukselt, sonra .\build_release.ps1
# Cikti: release\JamDeck-v{X}-win64.zip  (zip koku "JamDeck\" klasoru —
# uygulamadaki guncelleyicinin stage_zip() fonksiyonunun bekledigi yapi)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# 1) surumu tek kaynaktan oku
$verLine = Select-String -Path "backend\version.py" -Pattern 'APP_VERSION\s*=\s*"([^"]+)"'
if (-not $verLine) { Write-Error "backend\version.py icinde APP_VERSION bulunamadi"; exit 1 }
$ver = $verLine.Matches[0].Groups[1].Value
Write-Host "JamDeck v$ver paketleniyor..." -ForegroundColor Cyan

# 2) exe surum metadata'si (SmartScreen/UAC pencerelerinde "JamDeck" gorunur,
#    itibar sistemlerine tutarli urun kimligi sinyali verir)
$v4 = "$ver.0"; $vTuple = ($v4 -split '\.') -join ', '
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($vTuple), prodvers=($vTuple), mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'tarikyzco'),
      StringStruct('FileDescription', 'JamDeck - Game Jam Manager'),
      StringStruct('FileVersion', '$v4'),
      StringStruct('InternalName', 'JamDeck'),
      StringStruct('LegalCopyright', '(c) 2026 tarikyzco'),
      StringStruct('OriginalFilename', 'JamDeck.exe'),
      StringStruct('ProductName', 'JamDeck'),
      StringStruct('ProductVersion', '$v4')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | Out-File -Encoding utf8 "version_info.txt"

# 3) temiz build
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
pyinstaller "JamDeck.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller basarisiz (exit $LASTEXITCODE)"; exit 1 }
if (-not (Test-Path "dist\JamDeck\JamDeck.exe")) {
    Write-Error "dist\JamDeck\JamDeck.exe uretilmedi"; exit 1
}

# 3) zip (kok klasor dahil) — guncelleyicinin indirdigi asset BU; her release'te sart
if (-not (Test-Path "release")) { New-Item -ItemType Directory "release" | Out-Null }
$zip = "release\JamDeck-v$ver-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "dist\JamDeck" -DestinationPath $zip
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
