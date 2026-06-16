import base64
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from difflib import SequenceMatcher
from pathlib import Path

APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))  # paket içi (salt-okunur) kaynaklar


def data_dir() -> Path:
    """Yazılabilir kullanıcı verisi yolu — frozen (.exe) build'de _internal'a YAZILMAZ.
    Tüm config/oy/erişim/log dosyaları burada yaşar: %LOCALAPPDATA%\\JamDeck\\data.
    (Kök neden: PyInstaller _internal dizini yazmaya kapalı → FileNotFoundError →
    PyWebView köprüsünde sessizce yutulup UI'ı sonsuza dek asıyordu.)"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "JamDeck", "data")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    return Path(d)


DATA_DIR = data_dir()


def _migrate_state_file(name: str):
    """Eski sürüm dosyasını (backend yanı) yeni veri dizinine bir kez taşı/kopyala."""
    new = DATA_DIR / name
    if new.exists():
        return
    old = APP_DIR / name
    try:
        if old.exists() and old.resolve() != new.resolve():
            shutil.copy2(old, new)
    except OSError:
        pass


for _f in ("jam_settings.json", "game_overrides.json", "votes.json", "access.json"):
    _migrate_state_file(_f)

CONFIG_FILE = DATA_DIR / "jam_settings.json"


def _i18n_file() -> Path:
    """Tek kaynak çeviri dosyası — dev'de proje kökü/frontend, frozen'da _MEIPASS/frontend."""
    base = Path(getattr(sys, "_MEIPASS", APP_DIR.parent))
    return base / "frontend" / "i18n.js"


_I18N_CACHE = None


def load_i18n() -> dict:
    """frontend/i18n.js'i (lang -> {app, voter, countdown}) önbellekli döndürür.

    Dosya tek kaynaktır; tarayıcı <script src> ile, Python ise `window... = {…};`
    sarmalayıcısının içindeki JSON gövdesini ayıklayarak okur.
    """
    global _I18N_CACHE
    if _I18N_CACHE is None:
        try:
            with open(_i18n_file(), "r", encoding="utf-8") as f:
                txt = f.read()
            _I18N_CACHE = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        except Exception:
            _I18N_CACHE = {}
    return _I18N_CACHE


def i18n_section(section: str, lang: str) -> dict:
    """Belirli bir bölümü (app/voter/countdown) verilen dil için döndürür; tr'ye düşer."""
    data = load_i18n()
    src = data.get(lang) or data.get("tr") or {}
    return src.get(section, {})


def localize_vote_defaults(voting_cfg: dict, lang: str) -> dict:
    """Varsayılan kategori/grup etiketlerini verilen dile çevirir (yerinde).

    Bir etiket, herhangi bir dildeki varsayılana eşitse 'değiştirilmemiş varsayılan'
    sayılır ve o anki dile çevrilir; kullanıcının yazdığı özel adlar korunur.
    """
    if not voting_cfg:
        return voting_cfg
    data = load_i18n()
    cat_sets, grp_sets = {}, {}
    for d in data.values():
        vd = (d or {}).get("vote_defaults", {})
        for cid, lbl in (vd.get("cat") or {}).items():
            cat_sets.setdefault(cid, set()).add(lbl)
        for gid, lbl in (vd.get("grp") or {}).items():
            grp_sets.setdefault(gid, set()).add(lbl)
    cur = (data.get(lang) or data.get("tr") or {}).get("vote_defaults", {})
    cur_cat, cur_grp = cur.get("cat", {}), cur.get("grp", {})
    for c in voting_cfg.get("categories", []) or []:
        cid = c.get("id")
        if cid in cat_sets and c.get("label") in cat_sets[cid] and cid in cur_cat:
            c["label"] = cur_cat[cid]
    for gid, g in (voting_cfg.get("groups", {}) or {}).items():
        if gid in grp_sets and (g or {}).get("label") in grp_sets[gid] and gid in cur_grp:
            g["label"] = cur_grp[gid]
    return voting_cfg

BANNED_EXES = {
    "UnityCrashHandler64.exe", "UnityCrashHandler.exe",
    "Uninstall.exe", "unins000.exe", "dxwebsetup.exe",
    "createdump.exe", "adb.exe", "python.exe",
    "vc_redist.x64.exe", "vcredist_x64.exe",
    "UE4PrereqSetup_x64.exe", "SanityCheck.exe",
    "AyazJam_Manager.exe", "JamDeck.exe",
}

DEFAULT_CONFIG = {
    "jam": {
        "name": "My Game Jam",
        "tagline": "Game Jam",
        "logo": None,
        "background": None,
        "language": "en",
        "nameFont": "",
        "taglineFont": "",
    },
    "theme": {
        "preset": "frostbite",
        "colors": {
            "bg": "#050a14", "bg2": "#080e1c", "surface": "#0f1629",
            "surface2": "#141d33", "border": "#1e293b",
            "accent": "#00f2ff", "accent2": "#0062ff",
            "text": "#ffffff", "textMuted": "#94a3b8",
            "success": "#00e676", "warning": "#ffab00", "error": "#ff1744",
        },
        "radius": 18,
        "glow": 1.0,
    },
    "effect": {"name": "snow", "intensity": 150, "enabled": True},
    "launcher": {
        "defaultMinutes": 5,
        "onTimeUp": "kill",
        "killDelay": 3,
        "timerOverlay": True,
        "kioskLock": True,
    },
    "paths": {"gamesDir": str(Path.home() / "JamGames")},
    # itch.io indirme alanları — boş başlar, kullanıcı girince hatırlanır
    "itch": {"jamUrl": "", "apiKey": ""},
    "voting": {
        "enabled": False,
        "port": 8770,
        "mode": "internet",   # "internet" (önerilen) | "lan" — Başlat'ta hangi yol
        "scale": 10,
        "categories": [
            {"id": "overall",     "label": "Genel",        "weight": 30, "enabled": True},
            {"id": "fun",         "label": "Eğlence",      "weight": 25, "enabled": True},
            {"id": "theme",       "label": "Tema Uyumu",   "weight": 15, "enabled": True},
            {"id": "originality", "label": "Özgünlük",     "weight": 12, "enabled": True},
            {"id": "art",         "label": "Görsel/Sanat", "weight": 10, "enabled": True},
            {"id": "audio",       "label": "Ses/Müzik",    "weight": 8,  "enabled": True},
        ],
        "groups": {
            "jury":     {"enabled": True, "weight": 60, "label": "Jüri",
                         "access": "codes", "pin": "", "limit": 5,  "codeCount": 5},
            "audience": {"enabled": True, "weight": 25, "label": "Seyirci",
                         "access": "open",  "pin": "", "limit": 0,  "codeCount": 0},
            "team":     {"enabled": True, "weight": 15, "label": "Ekip",
                         "access": "codes", "pin": "", "limit": 30, "codeCount": 30},
        },
        # per-IP rate limit on vote/access POSTs (anti-spam, mainly for open audience)
        "rateLimit": {"enabled": True, "windowSec": 10, "max": 8},
    },
    # Teslim Kılavuzu metin override'ları; boş = yerleşik i18n varsayılanları
    "guide": {},
    # Geri sayım sahnesi (mekan ekranı): armed=True iken başlamaya 10 dk kala
    # uygulama hangi ekranda olursa olsun tam ekran sahneye geçer
    "countdown": {
        "armed": False,
        "startAt": "",          # ISO "YYYY-MM-DDTHH:MM" (datetime-local değeri)
        "durationHours": 48,
        "style": "neon",        # neon | minimal | segment | flip | terminal
        "logoLeft": None,       # dataUrl; None = boş
        "logoCenter": None,     # None -> jam.logo kullanılır
        "logoRight": None,
    },
    # Güncelleme: GitHub Releases'tan denetle/indir/kur (repo version.py'de gömülü)
    "update": {"auto": True},
}


def _deep_merge(base, override):
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


ARCHIVE_EXTS = (".zip", ".rar", ".7z", ".tar.gz", ".tgz", ".tar", ".tar.bz2", ".tar.xz")
_TAR_EXTS = (".tar.gz", ".tgz", ".tar", ".tar.bz2", ".tar.xz")
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _find_winrar():
    which = shutil.which("WinRAR") or shutil.which("Rar")
    if which:
        return which
    for p in [
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        r"D:\Program Files\WinRAR\WinRAR.exe",
    ]:
        if os.path.exists(p):
            return p
    return None


def _find_7zip():
    """Locate a 7-Zip CLI (handles zip/rar/7z + more with proper return codes)."""
    which = shutil.which("7z") or shutil.which("7za")
    if which:
        return which
    for p in [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        r"C:\Program Files\7-Zip\7za.exe",
        r"C:\Program Files (x86)\7-Zip\7za.exe",
    ]:
        if os.path.exists(p):
            return p
    return None


def _extract_archive(arch, dest, sevenzip=None, winrar=None):
    """Extract one archive (zip/rar/7z/...) into dest. Tries multiple backends and
    returns True on the first success. Order: native zipfile (zip) -> 7-Zip CLI ->
    WinRAR CLI -> py7zr (7z, pure-python) -> shutil. dest is created if missing."""
    os.makedirs(dest, exist_ok=True)
    low = arch.lower()

    # 0) tar family (.tar/.tar.gz/.tgz/...) — shutil extracts in one shot
    if low.endswith(_TAR_EXTS):
        try:
            shutil.unpack_archive(arch, dest)
            return True
        except Exception:
            pass

    # 1) native zip (fast, no external process)
    if low.endswith(".zip"):
        try:
            with zipfile.ZipFile(arch, "r") as z:
                z.extractall(dest)
            return True
        except Exception:
            pass

    # 2) 7-Zip / 3) WinRAR — both extract zip/rar/7z
    cli = [
        (sevenzip, [sevenzip, "x", "-y", "-bso0", "-bsp0", "-bse0", arch, "-o" + dest]),
        (winrar,   [winrar, "x", "-y", "-ibck", "-inul", "-o+", arch, dest + os.sep]),
    ]
    for tool, cmd in cli:
        if not tool:
            continue
        try:
            if subprocess.run(cmd, creationflags=_NO_WINDOW,
                              capture_output=True).returncode == 0:
                return True
        except Exception:
            pass

    # 4) py7zr — pure-python .7z fallback (no binary needed)
    if low.endswith(".7z"):
        try:
            import py7zr
            with py7zr.SevenZipFile(arch, "r") as z:
                z.extractall(path=dest)
            return True
        except Exception:
            pass

    # 5) last resort (zip/tar)
    try:
        shutil.unpack_archive(arch, dest)
        return True
    except Exception:
        return False


def _similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _detect_engine(folder):
    for root, dirs, files in os.walk(folder):
        for d in dirs:
            if d.endswith("_Data"):
                return "unity"
        for f in files:
            low = f.lower()
            if low.endswith(".pck"):
                return "godot"
            if low in ("ue4game.exe", "ue5game.exe"):
                return "unreal"
            if low in ("gamemaker_game.dll",):
                return "gamemaker"
    return "other"


def _image_to_data_url(path):
    ext = Path(path).suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp",
    }
    mime = mime_map.get(ext, "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{data}"


def _find_cover(folder):
    # Prefer the itch-dl cover (literally named cover.*) so a stray screenshot
    # from the extracted game files can't get picked as the cover.
    names = os.listdir(folder)
    for f in names:
        stem, ext = os.path.splitext(f.lower())
        if stem == "cover" and ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            return os.path.join(folder, f)
    for f in names:
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            return os.path.join(folder, f)
    return None


def _folder_has_exe(folder):
    """True if folder contains a launchable .exe (ignoring banned/console exes)."""
    for r, _, files in os.walk(folder):
        for f in files:
            if f.endswith(".exe") and f not in BANNED_EXES and "console" not in f.lower():
                return True
    return False


# files that are metadata/sidecars, not actual game content — ignored when
# deciding whether a folder is "just a wrapper" to flatten.
def _is_sidecar(name):
    low = name.lower()
    return (low in ("metadata.json", "site.html", ".broken")
            or low.startswith("cover.") or low == "__macosx")


def _find_web_index(folder):
    """Directory of the shallowest index.html (a web/HTML5 build), or None.
    itch's scraped page is site.html, so it is never matched here."""
    best, best_depth = None, 1 << 30
    for r, _, files in os.walk(folder):
        for f in files:
            if f.lower() == "index.html":
                depth = os.path.relpath(r, folder).count(os.sep)
                if depth < best_depth:
                    best, best_depth = r, depth
    return best


def _folder_has_web(folder):
    return _find_web_index(folder) is not None


def _find_browser():
    """A Chromium browser (Chrome/Edge) we can launch as a controllable kiosk
    window. Edge ships with Windows, so this practically always resolves."""
    for c in ("chrome", "msedge"):
        w = shutil.which(c)
        if w:
            return w
    for p in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.exists(p):
            return p
    return None


def _is_itch_files_dir(arch):
    """itch-dl puts downloads in <slug>/files/. Returns the slug dir if this
    archive lives in such a 'files' folder next to a metadata.json, else None."""
    parent = os.path.dirname(arch)
    slug = os.path.dirname(parent)
    if os.path.basename(parent) == "files" and os.path.exists(os.path.join(slug, "metadata.json")):
        return slug
    return None


def _extract_all_in(folder, sevenzip, winrar, on_extract=None, on_fail=None, max_rounds=6):
    """Extract every archive inside folder, repeatedly, to resolve nested archives.
    Each archive extracts into its own directory — except itch <slug>/files/<arch>,
    which extracts into the slug root. The archive is deleted on success. Stops when
    a round makes no progress (a failing archive won't loop forever) or after
    max_rounds (guards against archive bombs). Returns count extracted."""
    total = 0
    for _ in range(max_rounds):
        archives = [os.path.join(r, f)
                    for r, _, fs in os.walk(folder)
                    for f in fs if f.lower().endswith(ARCHIVE_EXTS)]
        if not archives:
            break
        progressed = False
        for arch in archives:
            if not os.path.exists(arch):
                continue
            dest = _is_itch_files_dir(arch) or os.path.dirname(arch)
            name = os.path.basename(arch)
            if _extract_archive(arch, dest, sevenzip, winrar):
                try:
                    os.remove(arch)
                except Exception:
                    pass
                total += 1
                progressed = True
                if on_extract:
                    on_extract(name)
            else:
                if on_fail:
                    on_fail(name)
        if not progressed:
            break
    return total


def _cleanup_folder(folder):
    """Drop __MACOSX and the scraped site.html, and an empty files/ dir."""
    for junk in ("__MACOSX", "site.html"):
        p = os.path.join(folder, junk)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass
    fdir = os.path.join(folder, "files")
    try:
        if os.path.isdir(fdir) and not os.listdir(fdir):
            os.rmdir(fdir)
    except Exception:
        pass


def _flatten_folder(folder):
    """Pull game content up out of a single redundant wrapper subfolder, keeping
    sidecars (metadata.json/cover.*) at the folder root. Returns fixes applied."""
    fixed = 0
    while True:
        items = [i for i in os.listdir(folder) if i != "__MACOSX"]
        subdirs = [i for i in items if os.path.isdir(os.path.join(folder, i))]
        real_files = [i for i in items
                      if os.path.isfile(os.path.join(folder, i)) and not _is_sidecar(i)]
        if len(subdirs) == 1 and not real_files:
            inner = os.path.join(folder, subdirs[0])
            for c in os.listdir(inner):
                src, dst = os.path.join(inner, c), os.path.join(folder, c)
                try:
                    if os.path.exists(dst):
                        # keep the root sidecar (e.g. metadata.json); drop the inner dup
                        if os.path.isdir(src):
                            shutil.rmtree(src, ignore_errors=True)
                        else:
                            os.remove(src)
                    else:
                        shutil.move(src, folder)
                except Exception:
                    pass
            shutil.rmtree(inner, ignore_errors=True)
            fixed += 1
        else:
            break
    return fixed


def _engine_fixups(folder):
    """Rename the build .exe to what the engine expects so it launches: Unity
    (<X>_Data ↔ <X>.exe) and Godot (<X>.pck ↔ <X>.exe). Returns fixes applied."""
    exes, datas, pcks = [], [], []
    for r, ds, fs in os.walk(folder):
        for d in ds:
            if d.endswith("_Data"):
                datas.append((r, d))
        for f in fs:
            if f.endswith(".exe") and f not in BANNED_EXES and "console" not in f.lower():
                exes.append((r, f))
            elif f.endswith(".pck"):
                pcks.append((r, f))
    fixed = 0
    # Unity
    if len(exes) == 1 and len(datas) == 1 and exes[0][0] == datas[0][0]:
        exe_root, exe_name = exes[0]
        expected = datas[0][1].replace("_Data", ".exe")
        if exe_name != expected:
            try:
                os.rename(os.path.join(exe_root, exe_name), os.path.join(exe_root, expected))
                exes[0] = (exe_root, expected)
                fixed += 1
            except Exception:
                pass
    # Godot
    if len(exes) == 1 and len(pcks) == 1 and exes[0][0] == pcks[0][0]:
        exe_root, exe_name = exes[0]
        expected = pcks[0][1].replace(".pck", ".exe")
        if exe_name != expected:
            try:
                os.rename(os.path.join(exe_root, exe_name), os.path.join(exe_root, expected))
                fixed += 1
            except Exception:
                pass
    return fixed


class JamDeckAPI:
    def __init__(self):
        self._window = None
        self._games: dict = {}
        self._active_process = None
        self._cancel_dl = False
        self._timer_stop = threading.Event()
        self._active_overlay = None
        self._voting = None  # VotingServer instance (lazy)
        self._voting_info = {}
        self._tunnel = None  # Cloudflare quick tunnel (internet voting)
        self._active_game_id = None
        self._active_web_server = None   # local HTTP server for a running web game
        self._active_web_profile = None  # temp browser user-data-dir to clean up

    def set_window(self, window):
        self._window = window

    # ------------------------------------------------------------------ helpers

    def _log_exc(self, where, tb):
        """Frozen (.exe) build'de konsol olmadığından hataları diske yaz —
        %LOCALAPPDATA%\\JamDeck\\data\\app.log. Sessiz hataları teşhis edilebilir kılar."""
        try:
            with open(DATA_DIR / "app.log", "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + "[" + str(where) + "]\n"
                        + str(tb) + "\n")
        except OSError:
            pass

    def _emit(self, event: str, payload):
        if not self._window:
            return
        try:
            self._window.evaluate_js(
                f"window.JamDeck.emit({json.dumps(event)}, {json.dumps(payload)})"
            )
        except Exception as exc:
            print(f"[JamDeck _emit error] {exc}", flush=True)

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # only trust it if it has the new-format keys
                if "jam" in raw and "theme" in raw:
                    return _deep_merge(DEFAULT_CONFIG, raw)
            except Exception:
                pass
        return copy.deepcopy(DEFAULT_CONFIG)

    # ------------------------------------------------------------------ config

    def getConfig(self):
        cfg = self._load_config()
        if not CONFIG_FILE.exists():
            cfg["__firstRun"] = True
        return cfg

    def saveConfig(self, config):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return {"ok": True}

    def resetConfig(self):
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        return copy.deepcopy(DEFAULT_CONFIG)

    def exportConfig(self):
        import webview
        cfg = self._load_config()
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="jam_config.json",
            file_types=("JSON Files (*.json)",),
        )
        if not result:
            return {"ok": False}
        path = result if isinstance(result, str) else result[0]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def savePng(self, data_url, suggested_name="JamDeck_Kilavuz.png"):
        """Save a base64 data-URL (image/png) to a user-chosen file.

        Used by the in-app Guide screen to export a high-res shareable poster
        rendered on the frontend (SVG -> canvas -> dataURL). Replaces the old
        fragile ImageGrab screenshot approach.
        """
        import webview
        try:
            b64 = data_url.split(",", 1)[1] if "," in data_url else data_url
            raw = base64.b64decode(b64)
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested_name,
                file_types=("PNG Image (*.png)",),
            )
            if not result:
                return {"ok": False, "cancelled": True}
            path = result if isinstance(result, str) else result[0]
            if not path.lower().endswith(".png"):
                path += ".png"
            with open(path, "wb") as f:
                f.write(raw)
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def importConfig(self):
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("JSON Files (*.json)",),
        )
        if result and result[0]:
            try:
                with open(result[0], "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if "jam" in cfg and "theme" in cfg:
                    self.saveConfig(cfg)
                    return cfg
            except Exception as e:
                return {"error": str(e)}
        return self._load_config()

    # ------------------------------------------------------------------ file dialogs

    def pickImage(self, target):
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Image Files (*.png;*.jpg;*.jpeg;*.svg;*.gif;*.webp)",),
        )
        if result and result[0]:
            try:
                return {"path": result[0], "dataUrl": _image_to_data_url(result[0])}
            except Exception as e:
                return {"path": None, "dataUrl": None, "error": str(e)}
        return {"path": None, "dataUrl": None}

    def selectGamesFolder(self):
        import webview
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and result[0]:
            return {"path": result[0]}
        return {"path": self._load_config().get("paths", {}).get("gamesDir", "")}

    def openGamesFolder(self):
        path = self._load_config().get("paths", {}).get("gamesDir", "")
        if path and os.path.exists(path):
            os.startfile(path)
        return {"ok": True}

    # ------------------------------------------------------------------ download

    def startDownload(self, url, apiKey):
        self._cancel_dl = False

        def run():
            cfg = self._load_config()
            games_dir = cfg.get("paths", {}).get("gamesDir", str(Path.home() / "JamGames"))
            os.makedirs(games_dir, exist_ok=True)

            # itch-dl GÖMÜLÜ: frozen exe'de kendimizi "__itch-dl__" ile yeniden çağırırız
            # (bundled itch_dl.cli.run); dev'de "python -m itch_dl". Harici CLI / pip yok.
            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "__itch-dl__", url, "--api-key", apiKey]
            else:
                cmd = [sys.executable, "-m", "itch_dl", url, "--api-key", apiKey]

            self._emit("log", {"channel": "download", "level": "info", "line": f"Connecting to {url}…"})

            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            try:
                # Force UTF-8 decoding of itch-dl's output — game titles/progress
                # bars contain non-ASCII bytes that the Windows default codec
                # (cp1254 'charmap') chokes on ("can't decode byte 0x8e ...").
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=flags, cwd=games_dir,
                )
                self._active_process = proc
                current = 0
                total = 0

                for line in proc.stdout:
                    if self._cancel_dl:
                        proc.terminate()
                        self._emit("log", {"channel": "download", "level": "warning", "line": "Download cancelled"})
                        return

                    line = line.strip()
                    if not line:
                        continue

                    m = re.search(r"(\d+)/(\d+)", line)
                    if m:
                        c, t = int(m.group(1)), int(m.group(2))
                        if 0 < t < 2000:
                            current, total = c, t

                    spd_m = re.search(r"(\d+\.?\d*\s*[kKMGT]?B/s)", line)
                    speed_str = spd_m.group(1) if spd_m else ""

                    if "Downloading" in line or "downloading" in line:
                        name = re.sub(r"[Dd]ownloading\s*", "", line).strip()[:60]
                        self._emit("download:progress", {
                            "current": current, "total": total or 1,
                            "name": name, "speed": speed_str,
                        })
                    self._emit("log", {"channel": "download", "level": "info", "line": line})

                proc.wait()
                if proc.returncode == 0:
                    self._emit("log", {"channel": "download", "level": "success", "line": "All downloads complete ✓"})
                    self._emit("download:done", {"ok": True})
                    # Tek otomatik akış: indirme biter bitmez açma/düzenleme zincirlenir.
                    # organizeFiles kendi thread'ini açar ve aynı "organize" log
                    # kanalına yazar; bitince organize:done yayınlar.
                    self.organizeFiles()
                else:
                    self._emit("log", {"channel": "download", "level": "error",
                                       "line": f"itch-dl exited with code {proc.returncode}"})
                    self._emit("download:done", {"ok": False})
            except Exception as e:
                self._emit("log", {"channel": "download", "level": "error", "line": str(e)})
                self._emit("download:done", {"ok": False})

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True}

    def cancelDownload(self):
        self._cancel_dl = True
        if self._active_process and self._active_process.poll() is None:
            try:
                self._active_process.terminate()
            except Exception:
                pass
        return {"ok": True}

    # ------------------------------------------------------------------ verify

    def verifyArchives(self):
        def run():
            cfg = self._load_config()
            games_dir = cfg.get("paths", {}).get("gamesDir", "")
            if not os.path.exists(games_dir):
                self._emit("log", {"channel": "verify", "level": "error", "line": "Games directory not found"})
                self._emit("verify:done", {"ok": False})
                return

            winrar = _find_winrar()
            archives = [
                os.path.join(r, f)
                for r, _, files in os.walk(games_dir)
                for f in files
                if f.lower().endswith((".zip", ".rar"))
            ]
            total = len(archives)
            self._emit("log", {"channel": "verify", "level": "info",
                                "line": f"Checking {total} archive(s)…"})
            bad = 0
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            for i, arch in enumerate(archives, 1):
                name = os.path.basename(arch)
                ok = True
                try:
                    if arch.lower().endswith(".zip"):
                        with zipfile.ZipFile(arch, "r") as z:
                            ok = z.testzip() is None
                    elif arch.lower().endswith(".rar") and winrar:
                        ok = subprocess.run(
                            [winrar, "t", "-inul", arch], creationflags=flags
                        ).returncode == 0
                except Exception:
                    ok = False

                if ok:
                    self._emit("log", {"channel": "verify", "level": "success",
                                       "line": f"OK  [{i}/{total}] {name}"})
                else:
                    bad += 1
                    self._emit("log", {"channel": "verify", "level": "error",
                                       "line": f"BAD [{i}/{total}] {name}"})

            lvl = "warning" if bad else "success"
            self._emit("log", {"channel": "verify", "level": lvl,
                                "line": f"Done · {total - bad} OK, {bad} corrupt"})
            self._emit("verify:done", {"ok": True, "corrupt": bad})

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True}

    # ------------------------------------------------------------------ organize

    def organizeFiles(self):
        def run():
            cfg = self._load_config()
            games_dir = cfg.get("paths", {}).get("gamesDir", "")
            if not os.path.exists(games_dir):
                self._emit("log", {"channel": "organize", "level": "error",
                                   "line": "Games directory not found"})
                self._emit("organize:done", {"extracted": 0, "fixed": 0, "removed": 0})
                return

            def log(level, line):
                self._emit("log", {"channel": "organize", "level": level, "line": line})

            sevenzip = _find_7zip()
            winrar = _find_winrar()
            log("info", f"Scanning {games_dir}…")
            if sevenzip or winrar:
                tool = "7-Zip" if sevenzip else "WinRAR"
                log("info", f"Extractor: {tool} (zip/rar/7z)")
            else:
                log("warning", "7-Zip/WinRAR not found — only .zip can be opened "
                               "(.rar/.7z will be skipped). Install 7-Zip for full support.")

            extracted = 0
            fixed = 0
            removed = 0

            def on_extract(n):
                log("success", f"[EXTRACT] {n}")
            def on_fail(n):
                log("error", f"[SKIP] {n} — could not extract (missing tool or corrupt)")

            # Pass 0 — bare archives dropped directly in the games dir
            for entry in list(os.listdir(games_dir)):
                p = os.path.join(games_dir, entry)
                if os.path.isfile(p) and p.lower().endswith(ARCHIVE_EXTS):
                    dest = os.path.join(games_dir, os.path.splitext(entry)[0])
                    if _extract_archive(p, dest, sevenzip, winrar):
                        extracted += 1
                        on_extract(entry)
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                    else:
                        on_fail(entry)

            # Pass 1 — normalize every game folder
            for folder in list(os.listdir(games_dir)):
                fp = os.path.join(games_dir, folder)
                if not os.path.isdir(fp):
                    continue

                # 1) extract all archives inside (itch files/, nested, multi)
                extracted += _extract_all_in(fp, sevenzip, winrar,
                                             on_extract=on_extract, on_fail=on_fail)
                # 2) drop __MACOSX / site.html / empty files/
                _cleanup_folder(fp)
                # 3) pull game content out of a redundant wrapper folder
                n = _flatten_folder(fp)
                if n:
                    fixed += n
                    log("info", f"[FIX] flattened {folder}")
                # 4) engine-specific exe rename so it launches
                n = _engine_fixups(fp)
                if n:
                    fixed += n
                    log("info", f"[FIX] engine exe renamed in {folder}")
                # 5) broken flag — set if not playable (no exe AND no web build),
                #    clear if it now has one
                bp = os.path.join(fp, ".broken")
                if _folder_has_exe(fp) or _folder_has_web(fp):
                    if os.path.exists(bp):
                        try:
                            os.remove(bp)
                        except Exception:
                            pass
                else:
                    try:
                        with open(bp, "w") as f:
                            f.write("no_exe")
                    except Exception:
                        pass
                    removed += 1
                    log("warning", f"[BROKEN] {folder} flagged (no .exe found)")

            summary = {"extracted": extracted, "fixed": fixed, "removed": removed}
            log("success", f"Done ✓ {extracted} extracted, {fixed} fixed, {removed} flagged")
            self._emit("organize:done", summary)

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True}

    # ------------------------------------------------------------------ launcher

    def scanGames(self):
        cfg = self._load_config()
        games_dir = cfg.get("paths", {}).get("gamesDir", "")

        if not os.path.exists(games_dir):
            return []

        self._games = {}
        games = []
        overrides = self._load_overrides()

        for folder_name in sorted(os.listdir(games_dir)):
            folder_path = os.path.join(games_dir, folder_name)
            if not os.path.isdir(folder_path):
                continue

            candidates = []
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in {"Engine", "Binaries", "Support"}]
                for f in files:
                    if (f.endswith(".exe")
                            and f not in BANNED_EXES
                            and "console" not in f.lower()):
                        candidates.append(os.path.join(root, f))

            # web/HTML5 build (index.html, no exe) — playable via browser
            web_dir = _find_web_index(folder_path) if not candidates else None
            is_web = bool(web_dir)

            is_broken = os.path.exists(os.path.join(folder_path, ".broken"))
            if is_web:
                is_broken = False  # web games are playable, never "broken"
            if not candidates and not is_web and not is_broken:
                continue

            def _score(path, fp=folder_path, fn=folder_name):
                s = -os.path.relpath(path, fp).count(os.sep) * 500
                s += _similar(fn, os.path.splitext(os.path.basename(path))[0]) * 300
                try:
                    s += os.path.getsize(path) / 1024 / 1024
                except Exception:
                    pass
                return s

            if candidates:
                candidates.sort(key=_score, reverse=True)
            rel_exes = [os.path.relpath(c, folder_path) for c in candidates]

            cover = None
            cover_path = _find_cover(folder_path)
            if cover_path:
                try:
                    cover = _image_to_data_url(cover_path)
                except Exception:
                    pass

            clean = folder_name.replace("_", " ").replace("-", " ").strip()
            
            if candidates:
                exe_name = (
                    os.path.splitext(os.path.basename(candidates[0]))[0]
                    .replace("_", " ").replace("-", " ").strip()
                )
                game_name = (
                    clean
                    if len(exe_name) < 3 or exe_name.lower() in ("game", "start", "play")
                    else exe_name
                )
            else:
                exe_name = "N/A"
                game_name = clean

            # ---------------------------------------------
            # itch.io metadata (from itch-dl: <slug>/metadata.json)
            # title -> game name, author -> team. No more name.txt.
            # ---------------------------------------------
            meta_path = os.path.join(folder_path, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
                        meta = json.load(f)
                    if meta.get("title"):
                        game_name = meta["title"]
                    if meta.get("author"):
                        clean = meta["author"]
                except Exception:
                    pass
            # ---------------------------------------------

            gid = folder_name

            # manual override (organizer-corrected name/team) wins over everything
            ov = overrides.get(gid)
            if ov:
                if ov.get("game"):
                    game_name = ov["game"]
                if ov.get("team"):
                    clean = ov["team"]

            self._games[gid] = {"folder": folder_path, "candidates": candidates,
                                "name": game_name, "cover": cover,
                                "web": is_web, "index_dir": web_dir}

            games.append({
                "id": gid,
                "team": clean,
                "game": game_name,
                "cover": cover,
                "exes": rel_exes,
                "is_broken": is_broken,
                "is_web": is_web,
                "currentExe": 0,
                "engine": "web" if is_web else _detect_engine(folder_path),
            })

        return games

    # ------------------------------------------------------------------ overrides

    OVERRIDES_FILE = DATA_DIR / "game_overrides.json"

    def _load_overrides(self):
        try:
            if self.OVERRIDES_FILE.exists():
                with open(self.OVERRIDES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def setGameInfo(self, gameId, name="", team=""):
        """Persist an organizer correction of a game's display name / team. Used
        when a dev typed an ASCII/wrong title on itch (e.g. 'Olulere Gecit Yok')."""
        name = (name or "").strip()
        team = (team or "").strip()
        ov = self._load_overrides()
        entry = ov.get(gameId, {})
        if name:
            entry["game"] = name
        if team:
            entry["team"] = team
        if entry:
            ov[gameId] = entry
        try:
            with open(self.OVERRIDES_FILE, "w", encoding="utf-8") as f:
                json.dump(ov, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        if gameId in self._games and name:
            self._games[gameId]["name"] = name
        return {"ok": True}

    def launchGame(self, gameId, exeIndex, minutes):
        if gameId not in self._games:
            return {"ok": False, "error": "Game not found"}

        g = self._games[gameId]

        # Kill previous game / overlay / web server
        self._timer_stop.set()
        self._kill_overlay()
        self._stop_web_server()
        if self._active_process and self._active_process.poll() is None:
            self._kill_pid(self._active_process.pid)

        if g.get("web"):
            proc = self._launch_web(g)
            if proc is None:
                return {"ok": False, "error": "Web oyunu açılamadı (tarayıcı/dizin yok)"}
        else:
            exe_path = g["candidates"][int(exeIndex)]
            try:
                proc = subprocess.Popen(exe_path, cwd=os.path.dirname(exe_path))
            except Exception as e:
                return {"ok": False, "error": str(e)}

        web_httpd = self._active_web_server  # this launch's server (None for exe)
        self._active_process = proc
        self._active_game_id = gameId
        self._timer_stop.clear()

        # push the launched game to the voting screen (if server running)
        # NOTE: no cover — voter page only needs the name; large cover dataURLs
        # bloat /api/current and stall phones.
        if self._voting is not None and self._voting.is_running:
            g = self._games.get(gameId, {})
            try:
                self._voting.set_current({"id": gameId, "name": g.get("name") or gameId})
            except Exception:
                pass

        cfg = self._load_config()
        launcher = cfg.get("launcher", {})
        on_timeup = launcher.get("onTimeUp", "kill")
        kill_delay = 5 # Forced to 5 seconds per user request
        show_overlay = launcher.get("timerOverlay", True)
        accent = cfg.get("theme", {}).get("colors", {}).get("accent", "#00f2ff")

        def timer_run():
            # Wait dynamically until the game's window is visible
            if not self._wait_for_window(proc, timeout=60):
                if not self._timer_stop.is_set():
                    self._emit("game:closed", {})
                if web_httpd:
                    self._stop_web_server(web_httpd)
                return

            if show_overlay and not self._timer_stop.is_set():
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                try:
                    args = [sys.executable]
                    if sys.executable.lower().endswith("python.exe") or sys.executable.lower().endswith("pythonw.exe"):
                        args.append(sys.argv[0])
                    args.extend(["--overlay", str(minutes), accent])
                    self._active_overlay = subprocess.Popen(args, creationflags=flags)
                except Exception as e:
                    pass

            remaining = max(1, int(float(minutes) * 60))
            while remaining > 0 and not self._timer_stop.is_set():
                self._emit("timer:tick", {"remaining": remaining})
                time.sleep(1)
                remaining -= 1
                if proc.poll() is not None:
                    self._emit("game:closed", {})
                    self._kill_overlay()
                    if web_httpd:
                        self._stop_web_server(web_httpd)
                    return

            if self._timer_stop.is_set():
                self._kill_overlay()
                return

            self._emit("timer:tick", {"remaining": 0})
            self._emit("timer:timesup", {})

            if on_timeup == "kill":
                time.sleep(kill_delay)
                if proc.poll() is None:
                    self._kill_pid(proc.pid)
                self._emit("game:closed", {})

            self._kill_overlay()
            if web_httpd:
                self._stop_web_server(web_httpd)

        threading.Thread(target=timer_run, daemon=True).start()
        return {"ok": True}

    def stopGame(self):
        self._timer_stop.set()
        self._kill_overlay()
        self._stop_web_server()
        if self._active_process and self._active_process.poll() is None:
            self._kill_pid(self._active_process.pid)

        self._emit("game:closed", {})
        return {"ok": True}

    # ------------------------------------------------------------------ web games

    def _launch_web(self, g):
        """Serve a web/HTML5 build locally and open it in a controllable kiosk
        browser window. Returns the browser process (killed on time-up) or None."""
        browser = _find_browser()
        if not browser:
            return None
        index_dir = g.get("index_dir") or _find_web_index(g["folder"])
        if not index_dir:
            return None
        try:
            from backend.web_server import serve_folder
        except Exception:
            from web_server import serve_folder
        httpd, port = serve_folder(index_dir)
        url = f"http://127.0.0.1:{port}/index.html"
        tmp = tempfile.mkdtemp(prefix="jamdeck_web_")
        try:
            proc = subprocess.Popen([
                browser, f"--app={url}", "--start-fullscreen", "--new-window",
                "--no-first-run", "--no-default-browser-check",
                "--autoplay-policy=no-user-gesture-required",
                f"--user-data-dir={tmp}",
            ])
        except Exception:
            try:
                httpd.shutdown()
            except Exception:
                pass
            shutil.rmtree(tmp, ignore_errors=True)
            return None
        self._active_web_server = httpd
        self._active_web_profile = tmp
        return proc

    def _stop_web_server(self, server=None):
        """Shut down the running web-game server. With no arg, stops the current
        one and cleans its temp browser profile; with an explicit server, only
        stops that instance (used by a finishing timer thread, race-safe)."""
        srv = server or self._active_web_server
        if srv is not None:
            try:
                srv.shutdown()
            except Exception:
                pass
        if server is None or server is self._active_web_server:
            self._active_web_server = None
            if self._active_web_profile:
                shutil.rmtree(self._active_web_profile, ignore_errors=True)
                self._active_web_profile = None

    # ------------------------------------------------------------------ voting (LAN)

    def _voting_cfg(self):
        return self._load_config().get("voting", copy.deepcopy(DEFAULT_CONFIG["voting"]))

    def startVoting(self):
        # KRİTİK: tüm gövde try/except ile sarılı → ne olursa olsun JS'e {ok,error}
        # döner (asla reject/exception sızdırmaz). Aksi halde PyWebView köprüsünde
        # yutulan hata "Başlat"ı sonsuza dek asardı (frozen build'de gözlendi).
        try:
            try:
                from backend.voting_server import VotingServer
            except Exception:
                from voting_server import VotingServer
            cfg = self._voting_cfg()
            # voter sayfası organizatörün temasıyla servis edilir
            full_cfg = self._load_config()
            theme = full_cfg.get("theme", {}) or {}
            lang = (full_cfg.get("jam", {}) or {}).get("language", "tr")
            # değiştirilmemiş varsayılan kategori/grup etiketlerini jam diline çevir
            localize_vote_defaults(cfg, lang)
            brand = {
                "jamName": (full_cfg.get("jam", {}) or {}).get("name", ""),
                "colors": theme.get("colors", {}) or {},
                "radius": theme.get("radius"),
                "glow": theme.get("glow"),
                "language": lang,
            }
            if self._voting is not None and self._voting.is_running:
                self._voting.stop()
            self._voting = VotingServer()
            res = self._voting.start(port=int(cfg.get("port", 8770)), config=cfg, brand=brand)
            self._voting_info = res if res.get("ok") else {}
            if res.get("ok"):
                # NOT: Windows Firewall (LAN) kuralı KALDIRILDI — online oylama tünelden
                # (localhost) çalışır, loopback firewall'dan muaf → inbound kurala gerek yok.
                self._voting_info = res
                # if a game is already running, surface it immediately (name only)
                if self._active_game_id and self._active_game_id in self._games:
                    g = self._games[self._active_game_id]
                    try:
                        self._voting.set_current({"id": self._active_game_id,
                                                  "name": g.get("name") or self._active_game_id})
                    except Exception:
                        pass
            return res
        except Exception as e:
            import traceback
            self._log_exc("startVoting", traceback.format_exc())
            return {"ok": False, "error": "start_failed", "detail": str(e)}

    def stopVoting(self):
        self._stop_tunnel()
        if self._voting is not None:
            try:
                self._voting.stop()
            except Exception:
                pass
        self._voting_info = {}
        return {"ok": True}

    # ---------------------------------------------------- internet voting (Tailscale Funnel)
    def _tun(self):
        try:
            from backend import tunnel as tun
        except Exception:
            import tunnel as tun
        return tun

    def _stop_tunnel(self):
        had = self._tunnel
        self._tunnel = None
        if isinstance(self._voting_info, dict):
            self._voting_info.pop("publicUrl", None)
        # funnel kapatmayı UI'ı BLOKLAMADAN, ve yalnız gerçekten açıldıysa yap
        # (tailscale komutları yavaş/takılabilir → 'Durdur' butonu beklemesin)
        if had:
            def _off():
                try:
                    self._tun().funnel_stop()
                except Exception:
                    pass
            threading.Thread(target=_off, daemon=True).start()

    def getInternetVotingState(self):
        """Tailscale hazır mı? UI 'İnternet oylaması' açılmadan durumu gösterir."""
        try:
            return self._tun().tailscale_state()
        except Exception as e:
            return {"installed": False, "loggedIn": False, "url": None, "msg": str(e)}

    def startInternetVoting(self):
        """Yerel oylama sunucusunu Tailscale Funnel ile SABİT bir public adrese açar
        (https://makine.tailnet.ts.net — asla değişmez). Sonucu tunnel:ready{url} /
        tunnel:error{error,detail} olayıyla bildirir (asenkron)."""
        if self._voting is None or not self._voting.is_running:
            return {"ok": False, "error": "not_running"}
        if isinstance(self._voting_info, dict) and self._voting_info.get("publicUrl"):
            return {"ok": True, "url": self._voting_info["publicUrl"], "already": True}
        port = int(self._voting_info.get("port") or 8770)
        tun = self._tun()

        def run():
            try:
                # 1) Tailscale kurulu değilse launcher indirip kurar (tek UAC onayı)
                if not tun.tailscale_state()["installed"]:
                    self._emit("tunnel:progress", {"stage": "install", "pct": -1})
                    tun.ensure_tailscale(progress_cb=lambda pct: self._emit(
                        "tunnel:progress", {"stage": "install", "pct": pct}))
                # 2) giriş yoksa login akışını tetikle + organizatörün girişini bekle
                if not tun.tailscale_state()["loggedIn"]:
                    self._emit("tunnel:progress", {"stage": "login", "pct": -1})
                    tun.tailscale_up()
                    deadline = time.time() + 180
                    while time.time() < deadline:
                        time.sleep(3)
                        if tun.tailscale_state()["loggedIn"]:
                            break
                    else:
                        self._emit("tunnel:error", {"error": "tailscale_not_logged_in",
                                                    "detail": "login timeout"})
                        return
                # bağlanma sürerken oylama durdurulduysa funnel'ı hiç başlatma
                if self._voting is None or not self._voting.is_running:
                    return
                # 3) Funnel → sabit public adres
                self._emit("tunnel:progress", {"stage": "connect", "pct": -1})
                url = tun.funnel_start(port)
                self._tunnel = True
                if isinstance(self._voting_info, dict):
                    self._voting_info["publicUrl"] = url
                self._emit("tunnel:ready", {"url": url})
            except Exception as e:
                self._stop_tunnel()
                if e.__class__.__name__ == "FunnelNotEnabled":
                    self._emit("tunnel:error", {"error": "funnel_not_enabled",
                                                "enableUrl": getattr(e, "enable_url", ""),
                                                "detail": getattr(e, "detail", "")})
                else:
                    msg = str(e)
                    code = msg.split(":", 1)[0].strip()
                    self._emit("tunnel:error", {"error": code, "detail": msg})

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True}

    def stopInternetVoting(self):
        self._stop_tunnel()
        return {"ok": True}

    def openUrl(self, url):
        """Verilen URL'yi varsayılan tarayıcıda aç (Funnel etkinleştirme linki vb.)."""
        try:
            import webbrowser
            if isinstance(url, str) and url.startswith("http"):
                webbrowser.open(url)
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False}

    def getVotingStatus(self):
        if self._voting is not None and self._voting.is_running:
            info = dict(self._voting_info)
            info["running"] = True
            return info
        return {"running": False}

    def setVotingConfig(self, voting):
        # persist into the saved config + live-update the running server
        cfg = self._load_config()
        cfg["voting"] = voting
        self.saveConfig(cfg)
        if self._voting is not None and self._voting.is_running:
            try:
                self._voting.set_config(voting)
            except Exception:
                pass
        return {"ok": True}

    def getAccessCodes(self):
        """Per-group access mode + one-time codes (claimed flags) + seat usage.
        Only meaningful while the server is running (codes live in the server)."""
        if self._voting is not None and self._voting.is_running:
            try:
                return {"ok": True, "groups": self._voting.get_access_codes()}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "not_running"}

    def regenerateCodes(self, group):
        """Mint a fresh set of one-time codes for a group (old codes + their
        device bindings become invalid)."""
        if self._voting is not None and self._voting.is_running:
            try:
                return self._voting.regenerate_codes(group)
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "not_running"}

    def getResults(self):
        if self._voting is not None and self._voting.is_running:
            try:
                res = self._voting.get_results()
                cg = self._voting.current_game
                # surface the active game to the in-app screen (strip heavy cover)
                res["current_game"] = {"id": cg["id"], "name": cg.get("name")} if cg else None
                res["running"] = True
                return res
            except Exception as e:
                return {"error": str(e)}
        # Sunucu kapalı: yine de daha önce verilen oylar (votes.json) görünsün ki
        # organizatör sunucuyu başlatmadan inceleyip sıfırlayabilsin.
        try:
            from backend.voting_server import VotingServer
        except Exception:
            from voting_server import VotingServer
        try:
            cfg = self._voting_cfg()
            lang = (self._load_config().get("jam", {}) or {}).get("language", "tr")
            localize_vote_defaults(cfg, lang)
            srv = VotingServer()
            srv.config = cfg
            srv._load_votes()           # votes.json -> srv.votes (thread başlatmaz)
            if not srv.votes:
                return {"games": [], "running": False, "current_game": None}
            res = srv.get_results()
            res["running"] = False
            res["current_game"] = None
            return res
        except Exception as e:
            return {"games": [], "running": False, "current_game": None, "error": str(e)}

    def exportResults(self):
        """Save the detailed technical results as a formatted .xlsx the organizer
        picks the location for. The pretty themed visual is built/exported on the
        frontend (SVG->PNG); this is the audit/technical file only."""
        import webview
        if self._voting is None or not self._voting.is_running:
            return {"ok": False, "error": "not_running"}
        cfg = self._load_config()
        jam_name = (cfg.get("jam", {}).get("name") or "JamDeck")
        safe = re.sub(r"[^\w\-]+", "_", jam_name).strip("_") or "JamDeck"
        try:
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=f"{safe}_Sonuclar.xlsx",
                file_types=("Excel Workbook (*.xlsx)",),
            )
            if not result:
                return {"ok": False, "cancelled": True}
            path = result if isinstance(result, str) else result[0]
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self._voting.export_xlsx(path)
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def resetVotes(self):
        """Clear all collected votes. Works whether the server is running (clears
        the live server's memory + file) or stopped (empties votes.json on disk),
        so leftover test votes can be wiped before an event starts."""
        if self._voting is not None and self._voting.is_running:
            try:
                return self._voting.reset_votes()
            except Exception as e:
                return {"ok": False, "error": str(e)}
        # server stopped: clear the persisted file directly
        try:
            from backend.voting_server import VOTES_FILE
        except Exception:
            from voting_server import VOTES_FILE
        try:
            with open(VOTES_FILE, "w", encoding="utf-8") as f:
                f.write("[]")
        except IOError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True}

    # ------------------------------------------------------------- güncelleme
    # GitHub Releases tabanlı kendi kendini güncelleme. Mantık backend/updater.py'de
    # (pywebview'siz test edilir); burada sadece köprü + thread + emit var.

    def getAppInfo(self):
        try:
            from backend.version import APP_VERSION, UPDATE_REPO
        except ImportError:
            from version import APP_VERSION, UPDATE_REPO
        return {
            "version": APP_VERSION,
            "frozen": bool(getattr(sys, "frozen", False)),
            "repo": UPDATE_REPO,
        }

    def checkUpdate(self):
        try:
            from backend import updater
            from backend.version import APP_VERSION, UPDATE_REPO, is_newer
        except ImportError:
            import updater
            from version import APP_VERSION, UPDATE_REPO, is_newer
        r = updater.check_github(UPDATE_REPO)
        r["current"] = APP_VERSION
        r["hasUpdate"] = bool(r.get("ok") and r.get("latest") and is_newer(r["latest"], APP_VERSION))
        return r

    def downloadUpdate(self, asset_url):
        try:
            from backend import updater
        except ImportError:
            import updater

        def run():
            try:
                self._emit("update:progress", {"pct": 0, "mb": 0, "totalMb": 0})
                updater.download_asset(
                    asset_url,
                    progress_cb=lambda pct, mb, total: self._emit(
                        "update:progress", {"pct": pct, "mb": mb, "totalMb": total}),
                )
                self._update_zip = str(updater.ZIP_PATH)
                self._emit("update:ready", {})
            except Exception as e:
                self._emit("update:error", {"error": str(e) or "network"})

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True}

    def pickUpdateZip(self):
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False,
            file_types=("Zip Arşivi (*.zip)",),
        )
        if result and result[0]:
            self._update_zip = result[0]
            return {"ok": True, "path": result[0]}
        return {"ok": False, "cancelled": True}

    def applyUpdate(self):
        try:
            from backend import updater
        except ImportError:
            import updater
        if not getattr(sys, "frozen", False):
            return {"ok": False, "error": "dev_mode"}
        zip_path = getattr(self, "_update_zip", None)
        if not zip_path or not os.path.exists(zip_path):
            return {"ok": False, "error": "no_zip"}
        try:
            src = updater.stage_zip(zip_path)
        except ValueError:
            return {"ok": False, "error": "bad_zip"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        install_dir = Path(sys.executable).parent
        updater.backup_state(install_dir)
        # yeniden başlatılacak exe: YENİ sürümdeki ad (exe adı değişse de çalışır)
        new_exe = install_dir / (updater.find_exe(src) or Path(sys.executable).name)
        bat = updater.write_apply_bat(
            os.getpid(), src, install_dir, new_exe, zip_path=zip_path)
        updater.launch_bat(bat)

        def shutdown():
            time.sleep(0.7)
            # destroy ayrı thread'de: pywebview ana döngüsüyle kilitlenirse bile
            # os._exit KOŞULSUZ çalışır (kilitlenme yaşandı — bat sonsuz beklemişti;
            # bat tarafında da 30 sn'lik zorla-kapat sibobu var)
            def _destroy():
                try:
                    if self._window:
                        self._window.destroy()
                except Exception:
                    pass
            threading.Thread(target=_destroy, daemon=True).start()
            time.sleep(1.2)
            os._exit(0)

        threading.Thread(target=shutdown, daemon=True).start()
        return {"ok": True}

    # ------------------------------------------------------------- countdown
    # Sayaç sayfası: tarayıcı sekmesi / OBS Browser Source için lokal HTTP.
    # Sayfa /config.json'u poll ettiğinden launcher'daki değişiklikler canlı yansır.

    def _countdown_state(self):
        cfg = self._load_config()
        jam = cfg.get("jam", {})
        lang = jam.get("language", "tr")
        return {
            "countdown": cfg.get("countdown", {}),
            "jam": {"name": jam.get("name"), "logo": jam.get("logo"),
                    "language": lang},
            "theme": {"colors": cfg.get("theme", {}).get("colors", {})},
            # launcher'daki arka plan efekti tarayıcı/OBS sayfasına da yansısın
            "effect": cfg.get("effect", {}),
            # tek kaynak i18n.json'dan çözülmüş sayaç metinleri (pre/main/done/empty)
            "cdtext": i18n_section("countdown", lang),
        }

    def startCountdownServer(self):
        try:
            from backend.countdown_page import start_countdown_server
        except ImportError:
            from countdown_page import start_countdown_server
        try:
            from backend.voting_server import get_lan_ip
        except ImportError:
            from voting_server import get_lan_ip
        if not getattr(self, "_cd_httpd", None):
            try:
                self._cd_httpd, self._cd_port = start_countdown_server(self._countdown_state)
            except Exception as e:
                return {"ok": False, "error": str(e)}
        try:
            ip = get_lan_ip()
        except Exception:
            ip = "127.0.0.1"
        url = f"http://{ip}:{self._cd_port}/"
        return {"ok": True, "url": url, "transparentUrl": url + "?transparent=1"}

    def stopCountdownServer(self):
        httpd = getattr(self, "_cd_httpd", None)
        if httpd:
            try:
                httpd.shutdown()
            except Exception:
                pass
            self._cd_httpd = None
        return {"ok": True}

    def openCountdownPage(self):
        if not getattr(self, "_cd_httpd", None):
            r = self.startCountdownServer()
            if not r.get("ok"):
                return r
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{self._cd_port}/")
        return {"ok": True}

    def openGuide(self):
        try:
            guide_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guide_gui.py")
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            args = [sys.executable]
            if sys.executable.lower().endswith("python.exe") or sys.executable.lower().endswith("pythonw.exe"):
                args.append(sys.argv[0]) # For PyInstaller context compatibility if needed, but here we just need python to run it
            
            # Actually just running the python executable with the script is enough
            subprocess.Popen([sys.executable, guide_script], creationflags=flags)
        except Exception as e:
            self._emit("log", {"channel": "system", "level": "error", "line": f"Guide error: {e}"})
        return {"ok": True}

    def _kill_overlay(self):
        if getattr(self, "_active_overlay", None) and self._active_overlay.poll() is None:
            try:
                self._active_overlay.terminate()
            except Exception:
                pass

    def _kill_pid(self, pid):
        try:
            import psutil
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except Exception:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

    def _wait_for_window(self, proc, timeout=60):
        if sys.platform != "win32":
            time.sleep(3)
            return True
            
        import ctypes
        import ctypes.wintypes
        import psutil
        
        start_time = time.time()
        try:
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        except Exception:
            time.sleep(3)
            return True

        while time.time() - start_time < timeout:
            if proc.poll() is not None or getattr(self, "_timer_stop", threading.Event()).is_set():
                return False
                
            pids = set([proc.pid])
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    pids.add(child.pid)
            except psutil.NoSuchProcess:
                return False
                
            found_window = False
            def foreach_window(hwnd, lParam):
                nonlocal found_window
                if IsWindowVisible(hwnd):
                    pid = ctypes.wintypes.DWORD()
                    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value in pids:
                        found_window = True
                        return False
                return True
                
            EnumWindows(EnumWindowsProc(foreach_window), 0)
            
            if found_window:
                time.sleep(1) # Allow window to render its first frame
                return True
                
            time.sleep(0.5)
            
        return False
