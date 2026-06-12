"""Organize & Clean rewrite test — exercises the real extractor path with real
zip/7z archives and runs organizeFiles end-to-end over a temp games dir.

Run: python tests/organize_test.py
"""
import base64
import io
import json
import os
import subprocess
import sys
import tarfile
import time
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import api as A          # noqa: E402
from backend.api import JamDeckAPI, _find_7zip, _extract_archive  # noqa: E402

log = []
def check(name, ok, extra=""):
    log.append(("PASS" if ok else "FAIL") + f"  {name}" + (f" — {extra}" if extra else ""))

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

def w(path, data="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
    with open(path, mode) as f:
        f.write(data)

def make_zip(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        for n, c in entries.items():
            z.writestr(n, c)

def make_7z(path, entries, sevenzip):
    """Create a .7z at path with given {name: content} using the 7-Zip CLI."""
    staging = tempfile.mkdtemp(prefix="7zstage_")
    for n, c in entries.items():
        w(os.path.join(staging, n), c)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run([sevenzip, "a", "-t7z", os.path.abspath(path)] + list(entries.keys()),
                   cwd=staging, creationflags=A._NO_WINDOW, capture_output=True)


sevenzip = _find_7zip()
check("7-Zip detected", bool(sevenzip), str(sevenzip))

# ---------------------------------------------------- unit: _extract_archive
tmpu = tempfile.mkdtemp(prefix="jamdeck_unit_")
zpath = os.path.join(tmpu, "a.zip")
make_zip(zpath, {"Game.exe": "MZ"})
d1 = os.path.join(tmpu, "out_zip")
check("_extract_archive zip", _extract_archive(zpath, d1, sevenzip, None)
      and os.path.exists(os.path.join(d1, "Game.exe")))
if sevenzip:
    spath = os.path.join(tmpu, "a.7z")
    make_7z(spath, {"Game7.exe": "MZ"}, sevenzip)
    d2 = os.path.join(tmpu, "out_7z")
    check("_extract_archive 7z", _extract_archive(spath, d2, sevenzip, None)
          and os.path.exists(os.path.join(d2, "Game7.exe")))


# ---------------------------------------------------- end-to-end organizeFiles
games = tempfile.mkdtemp(prefix="jamdeck_org_")

# A) itch slug, build is a .7z inside files/
a = os.path.join(games, "slug_basic")
w(os.path.join(a, "metadata.json"), json.dumps({"title": "Basic", "author": "Dev A"}))
w(os.path.join(a, "cover.png"), PNG)
if sevenzip:
    make_7z(os.path.join(a, "files", "build.7z"), {"Game.exe": "MZ", "Game_Data": "x"}, sevenzip)

# B) itch slug, nested zip-in-zip inside files/
b = os.path.join(games, "slug_nested")
w(os.path.join(b, "metadata.json"), json.dumps({"title": "Nested", "author": "Dev B"}))
inner = io.BytesIO()
with zipfile.ZipFile(inner, "w") as z:
    z.writestr("Deep.exe", "MZ")
make_zip(os.path.join(b, "files", "outer.zip"), {"inner.zip": inner.getvalue()})

# C) itch slug, bare exe inside files/ (no archive)
c = os.path.join(games, "slug_bare")
w(os.path.join(c, "metadata.json"), json.dumps({"title": "Bare", "author": "Dev C"}))
w(os.path.join(c, "files", "Bare.exe"), "MZ")

# D) broken: no exe, no archive
d = os.path.join(games, "brokengame")
w(os.path.join(d, "readme.txt"), "hello")

# E) itch slug, build is a .tar.gz inside files/
e = os.path.join(games, "slug_tar")
w(os.path.join(e, "metadata.json"), json.dumps({"title": "Tarred", "author": "Dev E"}))
_tstage = tempfile.mkdtemp(prefix="tarstage_")
w(os.path.join(_tstage, "TarGame.exe"), "MZ")
os.makedirs(os.path.join(e, "files"), exist_ok=True)
with tarfile.open(os.path.join(e, "files", "build.tar.gz"), "w:gz") as tf:
    tf.add(os.path.join(_tstage, "TarGame.exe"), arcname="TarGame.exe")

api = JamDeckAPI()
events = []
api._emit = lambda ev, payload: events.append((ev, payload))
api._load_config = lambda: {"paths": {"gamesDir": games}}

def run_and_wait():
    events.clear()
    api.organizeFiles()
    deadline = time.time() + 25
    while time.time() < deadline:
        if any(ev == "organize:done" for ev, _ in events):
            return next(p for ev, p in events if ev == "organize:done")
        time.sleep(0.2)
    return None

summary = run_and_wait()
check("organize:done emitted", summary is not None, str(summary))

if sevenzip:
    check("A: 7z extracted to slug root", os.path.exists(os.path.join(a, "Game.exe")))
    check("A: metadata + cover preserved",
          os.path.exists(os.path.join(a, "metadata.json")) and os.path.exists(os.path.join(a, "cover.png")))
    check("A: files/ removed", not os.path.exists(os.path.join(a, "files")))

check("B: nested zip fully extracted", os.path.exists(os.path.join(b, "Deep.exe")))
check("B: no leftover archives", not any(
    f.lower().endswith(A.ARCHIVE_EXTS) for r, _, fs in os.walk(b) for f in fs))

check("C: bare exe flattened to slug root", os.path.exists(os.path.join(c, "Bare.exe")))
check("C: files/ removed", not os.path.exists(os.path.join(c, "files")))

check("D: broken flagged", os.path.exists(os.path.join(d, ".broken")))

check("E: tar.gz extracted to slug root", os.path.exists(os.path.join(e, "TarGame.exe")))
check("E: files/ removed", not os.path.exists(os.path.join(e, "files")))

check("no stray top-level folder created", set(os.listdir(games)) ==
      {"slug_basic", "slug_nested", "slug_bare", "brokengame", "slug_tar"}, str(sorted(os.listdir(games))))

# broken -> fixed -> .broken cleared on re-run
w(os.path.join(d, "Fixed.exe"), "MZ")
run_and_wait()
check("D: .broken cleared after fix", not os.path.exists(os.path.join(d, ".broken")))

# end-to-end scan reads itch names
games_list = api.scanGames()
ga = next((g for g in games_list if g["id"] == "slug_basic"), {})
if sevenzip:
    check("scan: itch name+team after organize", ga.get("game") == "Basic" and ga.get("team") == "Dev A",
          f"game={ga.get('game')} team={ga.get('team')}")

print("\n=== ORGANIZE TEST ===")
print("\n".join(log))
fails = sum(1 for l in log if l.startswith("FAIL"))
print(f"\n{len(log)-fails}/{len(log)} passed")
sys.exit(1 if fails else 0)
