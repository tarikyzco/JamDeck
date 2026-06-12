"""JamDeck kendi kendini güncelleme mantığı (pywebview'siz, test edilebilir).

Akış: GitHub Releases'tan son sürüm denetlenir → zip asset %TEMP%'e indirilir →
zip Python'da açılır (stage) → kullanıcı durumu yedeklenir → bir .bat uygulama
kapanınca robocopy ile yeni sürümü kurar, JSON'ları geri yükler, uygulamayı
yeniden başlatır ve kendini siler.

Notlar:
- Zip bat içinde DEĞİL Python'da açılır (bat'ta PowerShell yok → AV dostu).
- Kullanıcı durumu dosyaları recursive aranır: frozen one-dir'de
  <dist>\\_internal\\backend\\ altında yaşarlar ama konum değişse de bulunur.
"""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# güncellemede asla kaybolmaması gereken kullanıcı durumu
STATE_FILES = ("jam_settings.json", "votes.json", "access.json", "game_overrides.json")

# yeni ad + eski sürümlerden gelen güncellemeler için eski ad da tanınır
EXE_CANDIDATES = ("JamDeck.exe", "Ayazjam Manager.exe")
EXE_NAME = EXE_CANDIDATES[0]

TMP = Path(tempfile.gettempdir())
ZIP_PATH = TMP / "jamdeck_update.zip"
STAGE_DIR = TMP / "jamdeck_update_new"
BACKUP_DIR = TMP / "jamdeck_update_backup"
BAT_PATH = TMP / "jamdeck_apply_update.bat"


# ------------------------------------------------------------------ denetim

def check_github(repo, timeout=6, api_base="https://api.github.com"):
    """repos/{repo}/releases/latest → {ok, latest, notes, assetUrl, assetSize, error}.

    GitHub, User-Agent başlıksız istekleri reddeder. Anonim limit 60 istek/saat —
    açılış denetimi tek istek olduğundan sorun değil; 403'te rate_limit döneriz.
    """
    repo = str(repo or "").strip().strip("/")
    if not repo or "/" not in repo:
        return {"ok": False, "error": "no_repo"}
    url = f"{api_base}/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={
        "User-Agent": "JamDeck-Updater",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"ok": False, "error": "no_release"}
        if e.code == 403:
            return {"ok": False, "error": "rate_limit"}
        return {"ok": False, "error": "network"}
    except Exception:
        return {"ok": False, "error": "network"}

    asset_url, asset_size = None, 0
    for a in data.get("assets", []):
        if str(a.get("name", "")).lower().endswith(".zip"):
            asset_url = a.get("browser_download_url")
            asset_size = a.get("size", 0)
            break
    return {
        "ok": True,
        "latest": data.get("tag_name", ""),
        "notes": data.get("body", "") or "",
        "assetUrl": asset_url,
        "assetSize": asset_size,
    }


# ------------------------------------------------------------------ indirme

def download_asset(url, dest=ZIP_PATH, progress_cb=None, cancel_flag=None):
    """Zip'i akışla indir; progress_cb(pct, mb, total_mb). Content-Length yoksa pct=-1."""
    req = urllib.request.Request(url, headers={"User-Agent": "JamDeck-Updater"})
    dest = Path(dest)
    with urllib.request.urlopen(req, timeout=30) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            while True:
                if cancel_flag and cancel_flag():
                    raise RuntimeError("cancelled")
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress_cb:
                    pct = round(done * 100 / total) if total else -1
                    progress_cb(pct, round(done / 1048576, 1), round(total / 1048576, 1))
    return dest


# ------------------------------------------------------------------ kurulum hazırlığı

def find_exe(folder):
    """Klasördeki uygulama exe'sinin adını döndür (yeni ya da eski ad), yoksa None."""
    for name in EXE_CANDIDATES:
        if (Path(folder) / name).exists():
            return name
    return None


def stage_zip(zip_path, stage_dir=STAGE_DIR):
    """Zip'i aç ve uygulama kökünü döndür. Kök tespiti toleranslı:
    exe doğrudan kökte ya da tek bir alt klasördeyse her ikisi de kabul."""
    stage_dir = Path(stage_dir)
    if stage_dir.exists():
        shutil.rmtree(stage_dir, ignore_errors=True)
    stage_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(stage_dir)
    if find_exe(stage_dir):
        return stage_dir
    subdirs = [d for d in stage_dir.iterdir() if d.is_dir()]
    for d in subdirs:
        if find_exe(d):
            return d
    raise ValueError("bad_zip")


def backup_state(install_dir, backup_dir=BACKUP_DIR):
    """STATE_FILES'ı kurulum klasöründe nerede olurlarsa olsunlar bul,
    göreli yolu koruyarak yedekle (bat en son geri kopyalar → kullanıcı kazanır)."""
    install_dir, backup_dir = Path(install_dir), Path(backup_dir)
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)
    found = 0
    for name in STATE_FILES:
        for p in install_dir.rglob(name):
            rel = p.relative_to(install_dir)
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            found += 1
    return found


# BAT notları (saha tecrübesiyle):
# - Bekleme döngüsünde PIPE YOK: `tasklist | find` boru hattı, uygulama tam o
#   anda ölürse find'ı sonsuza dek stdin bekletebiliyor (yaşandı). Geçici
#   dosya + findstr ile pipe'sız kontrol yapılır.
# - `timeout` yerine `ping -n N 127.0.0.1`: timeout, konsolsuz/yönlendirilmiş
#   ortamda "input redirection not supported" diye patlar; ping her yerde çalışır.
# - Emniyet sibobu: ~30 sn içinde kapanmazsa süreç zorla kapatılır, güncelleme sürer.
BAT_TEMPLATE = r"""@echo off
setlocal EnableDelayedExpansion
set "PID={pid}"
set "SRC={src_dir}"
set "DST={install_dir}"
set "BAK={backup_dir}"
set "EXE={exe_path}"
set "LOG=%TEMP%\jamdeck_update.log"
set "WTMP=%TEMP%\jamdeck_wait.tmp"
echo [%date% %time%] JamDeck guncelleme basliyor (PID %PID%) > "%LOG%"

set /a WTRIES=0
:waitloop
ping -n 2 127.0.0.1 >nul
tasklist /FI "PID eq %PID%" /NH > "%WTMP%" 2>nul
findstr /c:"%PID%" "%WTMP%" >nul 2>&1
if errorlevel 1 goto copyphase
set /a WTRIES+=1
if !WTRIES! GEQ 30 (
  echo Uygulama kapanmadi, zorla kapatiliyor >> "%LOG%"
  taskkill /PID %PID% /F >nul 2>&1
  ping -n 3 127.0.0.1 >nul
  goto copyphase
)
goto waitloop

:copyphase
del "%WTMP%" 2>nul
ping -n 2 127.0.0.1 >nul
set /a TRIES=0
:copyloop
robocopy "%SRC%" "%DST%" /E /R:2 /W:1 /NFL /NDL >> "%LOG%" 2>&1
if %ERRORLEVEL% GEQ 8 (
  set /a TRIES+=1
  if !TRIES! LSS 10 (
    ping -n 3 127.0.0.1 >nul
    goto copyloop
  )
  echo KOPYALAMA BASARISIZ - eski surum korunuyor >> "%LOG%"
  goto launch
)
echo Yeni surum kopyalandi >> "%LOG%"
if exist "%BAK%" (
  robocopy "%BAK%" "%DST%" /E /R:2 /W:1 /NFL /NDL >> "%LOG%" 2>&1
  echo Kullanici ayarlari geri yuklendi >> "%LOG%"
)

:launch
echo Uygulama yeniden baslatiliyor >> "%LOG%"
start "" "%EXE%"
rd /s /q "%SRC%" 2>nul
rd /s /q "%BAK%" 2>nul
del "{zip_path}" 2>nul
(goto) 2>nul & del "%~f0"
"""


def write_apply_bat(pid, src_dir, install_dir, exe_path,
                    backup_dir=BACKUP_DIR, zip_path=ZIP_PATH, bat_path=BAT_PATH):
    content = BAT_TEMPLATE.format(
        pid=pid, src_dir=src_dir, install_dir=install_dir,
        backup_dir=backup_dir, exe_path=exe_path, zip_path=zip_path,
    )
    bat_path = Path(bat_path)
    # cmd.exe Türkçe karakterli yolları cp1254/OEM bekler; ASCII dışına çıkmamak
    # için yollar zaten sistemden geliyor — yine de errors=replace ile garanti
    with open(bat_path, "w", encoding="cp1254", errors="replace", newline="\r\n") as f:
        f.write(content)
    return bat_path


def launch_bat(bat_path):
    # YALNIZ CREATE_NO_WINDOW: DETACHED_PROCESS ile birlikte kullanmak geçersiz
    # kombinasyon (ikisi de konsol bayrağı) — pencere görünmesine ve sürecin
    # uygulamaya bağlı kalmasına yol açmıştı (yaşandı).
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.Popen(["cmd", "/c", str(bat_path)],
                     creationflags=flags, close_fds=True,
                     cwd=tempfile.gettempdir())
