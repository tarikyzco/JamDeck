# Güncelleme altyapısı backend testleri: semver, check_github (lokal stub),
# stage_zip kök tespiti, backup_state recursive arama.
import json
import os
import shutil
import sys
import tempfile
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.version import parse_version, is_newer  # noqa: E402
from backend import updater  # noqa: E402

results = []


def step(name, ok, extra=""):
    results.append((name, ok, extra))
    print(("PASS  " if ok else "FAIL  ") + name + (f" — {extra}" if extra else ""))


# ---------- semver ----------
step("v2.1.0 > 2.0.0", is_newer("v2.1.0", "2.0.0"))
step("2.0.10 > 2.0.9", is_newer("2.0.10", "2.0.9"))
step("equal not newer", not is_newer("2.0.0", "v2.0.0"))
step("older not newer", not is_newer("1.9.9", "2.0.0"))
step("junk tolerated", parse_version("v2.x.1") == (2, 0, 1), str(parse_version("v2.x.1")))
step("short version padded", parse_version("3") == (3, 0, 0))

# ---------- check_github (stub sunucu) ----------
RELEASE_JSON = {
    "tag_name": "v9.9.9",
    "body": "Test notlari",
    "assets": [
        {"name": "readme.txt", "browser_download_url": "x", "size": 1},
        {"name": "JamDeck-v9.9.9-win64.zip",
         "browser_download_url": "http://example.com/a.zip", "size": 1234},
    ],
}


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if "noua" not in self.path and not self.headers.get("User-Agent"):
            self.send_error(403)
            return
        if self.path.endswith("/repos/ok/repo/releases/latest"):
            body = json.dumps(RELEASE_JSON).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.endswith("/repos/none/repo/releases/latest"):
            self.send_error(404)
        elif self.path.endswith("/repos/rate/repo/releases/latest"):
            self.send_error(403)
        else:
            self.send_error(500)


httpd = HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{httpd.server_address[1]}"

r = updater.check_github("ok/repo", api_base=base)
step("check ok + zip asset picked",
     r["ok"] and r["latest"] == "v9.9.9" and r["assetUrl"].endswith("a.zip")
     and r["assetSize"] == 1234, json.dumps(r))
r = updater.check_github("none/repo", api_base=base)
step("404 -> no_release", not r["ok"] and r["error"] == "no_release")
r = updater.check_github("rate/repo", api_base=base)
step("403 -> rate_limit", not r["ok"] and r["error"] == "rate_limit")
r = updater.check_github("")
step("empty repo -> no_repo", not r["ok"] and r["error"] == "no_repo")
r = updater.check_github("slugsuz")
step("slash-less repo -> no_repo", not r["ok"] and r["error"] == "no_repo")
r = updater.check_github("a/b", api_base="http://127.0.0.1:1", timeout=2)
step("unreachable -> network", not r["ok"] and r["error"] == "network")
httpd.shutdown()

# ---------- stage_zip ----------
tmp = Path(tempfile.mkdtemp())


def make_zip(name, inner_root, exe_name=updater.EXE_NAME):
    zp = tmp / name
    with zipfile.ZipFile(zp, "w") as z:
        prefix = f"{inner_root}/" if inner_root else ""
        z.writestr(f"{prefix}{exe_name}", b"exe")
        z.writestr(f"{prefix}_internal/frontend/index.html", b"<html>")
    return zp


stage = tmp / "stage1"
root = updater.stage_zip(make_zip("normal.zip", "JamDeck"), stage)
step("stage: normal root", (root / updater.EXE_NAME).exists() and root.name == "JamDeck")
stage = tmp / "stage2"
root = updater.stage_zip(make_zip("renamed.zip", "JamDeck-yeni"), stage)
step("stage: renamed root tolerated", (root / updater.EXE_NAME).exists())
stage = tmp / "stage3"
root = updater.stage_zip(make_zip("flat.zip", ""), stage)
step("stage: exe at zip root", (root / updater.EXE_NAME).exists() and root == stage)
stage = tmp / "stage_legacy"
root = updater.stage_zip(make_zip("legacy.zip", "Ayazjam Manager", "Ayazjam Manager.exe"), stage)
step("stage: legacy exe name tolerated", updater.find_exe(root) == "Ayazjam Manager.exe")
try:
    bad = tmp / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("rastgele.txt", b"x")
    updater.stage_zip(bad, tmp / "stage4")
    step("stage: bad zip raises", False)
except ValueError:
    step("stage: bad zip raises", True)

# ---------- backup_state ----------
install = tmp / "install" / "JamDeck"
(install / "_internal" / "backend").mkdir(parents=True)
for n in ("jam_settings.json", "votes.json"):
    (install / "_internal" / "backend" / n).write_text("{}", encoding="utf-8")
(install / "access.json").write_text("{}", encoding="utf-8")  # farklı konum da bulunmalı
bak = tmp / "bak"
found = updater.backup_state(install, bak)
step("backup finds state files recursively", found == 3, f"found={found}")
step("backup preserves relative paths",
     (bak / "_internal" / "backend" / "jam_settings.json").exists()
     and (bak / "access.json").exists())

# ---------- bat üretimi ----------
bat = updater.write_apply_bat(1234, tmp / "src", install, install / "JamDeck.exe",
                              backup_dir=bak, zip_path=tmp / "u.zip", bat_path=tmp / "apply.bat")
content = bat.read_text(encoding="cp1254")
step("bat: pid + quoted paths + robocopy + restore order",
     'set "PID=1234"' in content and 'robocopy "%SRC%" "%DST%"' in content
     and content.index('robocopy "%SRC%"') < content.index('robocopy "%BAK%"')
     and 'start "" "%EXE%"' in content)

shutil.rmtree(tmp, ignore_errors=True)
fails = [r for r in results if not r[1]]
print(f"\n{len(results)-len(fails)}/{len(results)} PASS")
sys.exit(1 if fails else 0)
